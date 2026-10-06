"""Bounded authenticated read API; no identity creation or scientific acceptance."""

import asyncio
import json

from amphora_contracts_graph_runtime import ReceiptCorrectionView
from amphora_contracts_research import (
    AssessmentPublicationRequest,
    AssessmentPublicationStatus,
    CorrectAssessmentReceipt,
    EvidenceAssessmentRequest,
    EvidenceAssessmentStatus,
    EvidenceNeed,
    EvidenceNeedRef,
    IdentityResolution,
    ResearchQuestion,
    ResearchQuestionRef,
    ResolveIdentity,
    SelectAssessmentReceipt,
)
from amphora_tool_protocol import ProtocolError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..evaluation_reuse.errors import ReuseError, ReusePeerUnavailable
from ..evaluation_reuse.routes import install_routes as install_reuse_routes
from ..fitness.policy import FitnessError
from ..fitness.reuse import EvaluationIdentityError
from ..fitness.routes import install_routes as install_fitness_routes
from ..observations.identity import ObservationError
from ..persistence.decision_document import DecisionStoreError
from ..assessment.policy import AssessmentError
from ..assessment.reader import AssessmentPeerUnavailable
from ..candidate_registration.profiles import CandidateRegistrationError
from ..candidate_registration.registration import CandidateReader
from ..candidate_registration.routes import install_routes as install_candidate_routes
from ..declarations.registration import DeclarationError
from ..identity.questions import ResearchIdentityError
from .access import AccessDenied
from .declarations import DeclarationReader


class InvalidRequest(ValueError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRequest("duplicate_json_key")
        result[key] = value
    return result


def _constant(_value):
    raise InvalidRequest("invalid_json_constant")


async def _body(request, limit=16384):
    parts = []
    count = 0
    async for part in request.stream():
        count += len(part)
        if count > limit:
            raise InvalidRequest("request_limit")
        parts.append(part)
    return b"".join(parts)


def create_app(resolver, credentials, assessments=None, science=None, registrar=None, candidates=None, fitness=None, reuse=None):
    app = FastAPI(title="Amphora Research", docs_url=None, redoc_url=None)
    app.state.declarations_enabled = registrar is not None
    app.state.reuse_enabled = reuse is not None
    app.state.fitness_enabled = fitness is not None
    app.state.candidates_enabled = candidates is not None
    app.state.assessment_enabled = assessments is not None
    app.state.science_enabled = science is not None
    app.state.authority = "synthetic_science" if science is not None else ("identity_only" if assessments is None else "synthetic_assessment")
    if science is not None:
        from ..scientific_api.routes import install_routes
        install_routes(app,credentials,science)

    @app.get("/health")
    def health():
        return {"service": "research", "authority": app.state.authority}

    async def invoke(request, model, operation, limit=16384):
        try:
            principal = credentials.authenticate(request.headers.get("authorization"))
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                return JSONResponse(status_code=415, content={"code": "json_required"})
            body = await asyncio.wait_for(_body(request, limit), timeout=5)
            decoded = json.loads(body.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
            # Parse in JSON mode so immutable tuple/schema rules match published wire contracts.
            query = model.model_validate_json(json.dumps(decoded))
            result = await asyncio.to_thread(operation, principal, query)
            if result is None:
                return JSONResponse(status_code=404, content={"code": "declaration_unavailable"},
                                    headers={"Cache-Control": "no-store"})
            return JSONResponse(content=result.model_dump(mode="json"), headers={"Cache-Control": "no-store"})
        except AccessDenied as error:
            status = 401 if str(error) == "unauthorized" else 403
            return JSONResponse(status_code=status, content={"code": str(error)})
        except InvalidRequest as error:
            return JSONResponse(status_code=413 if str(error) == "request_limit" else 422, content={"code": str(error)})
        except ReusePeerUnavailable:
            return JSONResponse(status_code=503,content={"code":"reuse_peer_unavailable"},headers={"Cache-Control":"no-store"})
        except (AssessmentPeerUnavailable, ProtocolError):
            return JSONResponse(status_code=503, content={"code": "assessment_peer_unavailable"})
        except AssessmentError as error:
            code = str(error)
            status = (403 if code in {"assessment_actor_mismatch", "peer_access_denied"} else
                      409 if "conflict" in code or code in {"publication_assessment_pending", "correction_publication_pending"} else
                      404 if code in {"assessment_profile_unavailable", "publication_assessment_missing"} else 422)
            return JSONResponse(status_code=status, content={"code": code}, headers={"Cache-Control": "no-store"})
        except (ReuseError, FitnessError, EvaluationIdentityError, ObservationError, DecisionStoreError) as error:
            code = str(error)
            status = (403 if "scope_mismatch" in code or "actor_mismatch" in code else
                      409 if "conflict" in code else 404 if code.endswith("_unavailable") else 422)
            return JSONResponse(status_code=status, content={"code":code}, headers={"Cache-Control":"no-store"})
        except CandidateRegistrationError as error:
            code = str(error)
            status = (403 if "scope_mismatch" in code or code == "peer_access_denied" else
                      409 if code in {"immutable_revision_conflict", "revision_head_conflict"} else
                      404 if code == "reference_unavailable" else 422)
            return JSONResponse(status_code=status, content={"code": code}, headers={"Cache-Control": "no-store"})
        except DeclarationError as error:
            code = str(error)
            status = (403 if "scope_mismatch" in code else
                      409 if code in {"immutable_revision_conflict", "revision_head_conflict"} else
                      404 if code == "unknown_question" else 422)
            return JSONResponse(status_code=status, content={"code": code}, headers={"Cache-Control": "no-store"})
        except (SQLAlchemyError, ResearchIdentityError):
            return JSONResponse(status_code=503, content={"code": "identity_owner_unavailable"})
        except (ValueError, UnicodeError, RecursionError, ValidationError):
            return JSONResponse(status_code=422, content={"code": "invalid_request"})
        except TimeoutError:
            return JSONResponse(status_code=408, content={"code": "request_timeout"})

    @app.post("/v1/identities/resolve", response_model=IdentityResolution)
    async def resolve(request: Request):
        return await invoke(request, ResolveIdentity, resolver.resolve)

    install_candidate_routes(app, invoke, CandidateReader(resolver.ledger), candidates)
    declarations = DeclarationReader(resolver.ledger)

    @app.post("/v1/questions/read", response_model=ResearchQuestion)
    async def question(request: Request):
        return await invoke(request, ResearchQuestionRef, declarations.read)

    @app.post("/v1/evidence-needs/read", response_model=EvidenceNeed)
    async def evidence_need(request: Request):
        return await invoke(request, EvidenceNeedRef, declarations.read)

    if assessments is not None:
        @app.post("/v1/assessments", response_model=EvidenceAssessmentStatus)
        async def assess(request: Request):
            return await invoke(request, EvidenceAssessmentRequest, assessments.submit, limit=262144)

        @app.post("/v1/assessments/read", response_model=EvidenceAssessmentStatus)
        async def read_assessment(request: Request):
            return await invoke(request, EvidenceAssessmentRequest, assessments.read, limit=262144)

        @app.post("/v1/assessment-publications", response_model=AssessmentPublicationStatus)
        async def publish_assessment(request: Request):
            return await invoke(request, AssessmentPublicationRequest, assessments.publish)

        @app.post("/v1/assessment-publications/read", response_model=AssessmentPublicationStatus)
        async def read_publication(request: Request):
            return await invoke(request, AssessmentPublicationRequest, assessments.read_publication)

        @app.post("/v1/assessment-receipts/correct", response_model=ReceiptCorrectionView)
        async def correct_receipt(request: Request):
            return await invoke(request, CorrectAssessmentReceipt, assessments.correct_receipt)

        @app.post("/v1/assessment-receipts/select", response_model=ReceiptCorrectionView)
        async def select_receipt(request: Request):
            return await invoke(request, SelectAssessmentReceipt, assessments.select_receipt)

    if registrar is not None:
        from ..declarations.routes import install_routes
        install_routes(app, invoke, registrar)

    install_fitness_routes(app, invoke, fitness)
    install_reuse_routes(app, invoke, reuse)
    return app
