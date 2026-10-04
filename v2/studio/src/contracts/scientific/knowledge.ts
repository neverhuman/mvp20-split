import schemas from "../generated/knowledge/schemas.json" with { type: "json" };
import type { GraphEntitySearchRequest } from "../generated/knowledge/search_request.js";
import type { GraphEntitySearchPage } from "../generated/knowledge/search_page.js";
import type { GraphNeighborhoodRequest } from "../generated/knowledge/neighborhood_request.js";
import type { GraphNeighborhoodPage } from "../generated/knowledge/neighborhood_page.js";
import type { GraphObjectRequest } from "../generated/knowledge/object_request.js";
import type { GraphObjectDetail } from "../generated/knowledge/object_detail.js";
import type { GraphExploreCatalog } from "../generated/knowledge/catalog.js";
import { decoder } from "./validation.js";

export type { GraphEntitySearchRequest, GraphEntitySearchPage, GraphNeighborhoodRequest, GraphNeighborhoodPage, GraphObjectRequest, GraphObjectDetail, GraphExploreCatalog };
export type DomainRevisionRef = GraphEntitySearchRequest["revision"];
export interface KnowledgeWire {
  search_request: GraphEntitySearchRequest;
  search_page: GraphEntitySearchPage;
  neighborhood_request: GraphNeighborhoodRequest;
  neighborhood_page: GraphNeighborhoodPage;
  object_request: GraphObjectRequest;
  object_detail: GraphObjectDetail;
  catalog: GraphExploreCatalog;
}
export const decodeKnowledge = decoder<KnowledgeWire>(schemas);
