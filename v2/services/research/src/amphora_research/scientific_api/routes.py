"""Optional bounded JSON routes; separate grants and operational errors preserve scientific meaning."""
import asyncio
import json

from amphora_contracts_research import (
    ExperimentRevisionRef,
    LabIntakeRequest,
    LabIntakeSelection,
    MaterialStateRevisionRef,
    ObservationRevisionRef,
    RegisterScientificConsumer,
    ScientificAssessmentRequest,
    ScientificConsumersRequest,
    ScientificDecisionRef,
    ScientificImpactRequest,
    ScientificPublicationRequest,
)
from amphora_tool_protocol import ProtocolError
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..assessment.policy import AssessmentError
from ..assessment.reader import AssessmentPeerUnavailable
from ..eligibility.evidence import EligibilityError
from ..observations.identity import ObservationError
from ..persistence.decision_document import DecisionStoreError
from ..persistence.revisions import ScientificStoreError
from ..scientific_publication.artifact import ScientificPublicationError
from ..synthesis.validation import SynthesisError
from ..transport.access import AccessDenied
from ..transport.api import InvalidRequest, _body, _constant, _unique
from .boundary import ScientificInputError


def response(code, status):
    return JSONResponse(status_code=status,content={"code":code},headers={"Cache-Control":"no-store"})


def install_routes(app, credentials, operations):
    async def invoke(request, model, operation):
        try:
            principal = credentials.authenticate(request.headers.get("authorization"))
            if request.headers.get("content-type","").split(";",1)[0].strip().lower() != "application/json":
                return response("json_required",415)
            body = await asyncio.wait_for(_body(request,262144),timeout=5)
            decoded = json.loads(body.decode("utf-8"),object_pairs_hook=_unique,parse_constant=_constant)
            query = model.model_validate_json(json.dumps(decoded))
            result = await asyncio.to_thread(operation,principal,query)
            if result is None:
                return response("scientific_record_unavailable",404)
            return JSONResponse(content=result.model_dump(mode="json"),headers={"Cache-Control":"no-store"})
        except AccessDenied as error:
            return response(str(error),401 if str(error) == "unauthorized" else 403)
        except InvalidRequest as error:
            return response(str(error),413 if str(error) == "request_limit" else 422)
        except (AssessmentPeerUnavailable,ProtocolError):
            return response("scientific_peer_unavailable",503)
        except SQLAlchemyError:
            return response("scientific_owner_unavailable",503)
        except (ScientificInputError,ScientificPublicationError,DecisionStoreError,ScientificStoreError,
                ObservationError,EligibilityError,SynthesisError,AssessmentError) as error:
            code = str(error)
            status = (403 if code == "peer_access_denied" or "actor_mismatch" in code else
                409 if "conflict" in code or "pending" in code or code == "science_intake_not_resolved" else
                404 if code in ("scientific_profile_unavailable","scientific_record_missing") else 422)
            return response(code,status)
        except (ValueError,UnicodeError,RecursionError):
            return response("invalid_request",422)
        except TimeoutError:
            return response("request_timeout",408)

    def register(path, model, operation):
        async def endpoint(request: Request):
            return await invoke(request,model,operation)
        app.add_api_route(path,endpoint,methods=["POST"],name=path.rsplit("/",1)[-1])

    for path,model,operation in (
        ("lab-intakes",LabIntakeRequest,operations.submit_lab),
        ("lab-intakes/read",LabIntakeSelection,operations.read_lab),
        ("scientific-assessments",ScientificAssessmentRequest,operations.submit_assessment),
        ("scientific-assessments/read",ScientificAssessmentRequest,operations.read_assessment),
        ("scientific-decisions/read",ScientificDecisionRef,operations.read_decision),
        ("material-states/read",MaterialStateRevisionRef,operations.read_material),
        ("experiments/read",ExperimentRevisionRef,operations.read_experiment),
        ("observations/read",ObservationRevisionRef,operations.read_observation),
        ("scientific-publications",ScientificPublicationRequest,operations.publications.submit),
        ("scientific-publications/read",ScientificPublicationRequest,operations.publications.read),
        ("scientific-impact",ScientificImpactRequest,operations.impact),
        ("scientific-consumers",RegisterScientificConsumer,operations.publications.register_consumer),
        ("scientific-consumers/read",ScientificConsumersRequest,operations.consumers),
    ):
        register("/v1/"+path,model,operation)
