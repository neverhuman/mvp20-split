import compiled from "../generated/research/validators.js";
import type { SpecimenViewRequest } from "../generated/research/specimen_request.js";
import type { SpecimenViewPage } from "../generated/research/specimen_page.js";
import type { PropertyViewRequest } from "../generated/research/property_request.js";
import type { PropertyViewPage } from "../generated/research/property_page.js";
import type { ObservationSeriesRequest } from "../generated/research/series_request.js";
import type { ObservationSeriesPage } from "../generated/research/series_page.js";
import type { ResearchViewCatalog } from "../generated/research/catalog.js";
import { decoder } from "./validation.js";

export type { SpecimenViewRequest, SpecimenViewPage, PropertyViewRequest, PropertyViewPage, ObservationSeriesRequest, ObservationSeriesPage, ResearchViewCatalog };
export type ExperimentRevisionRef = SpecimenViewRequest["experiment"];
export interface ResearchWire {
  specimen_request: SpecimenViewRequest;
  specimen_page: SpecimenViewPage;
  property_request: PropertyViewRequest;
  property_page: PropertyViewPage;
  series_request: ObservationSeriesRequest;
  series_page: ObservationSeriesPage;
  catalog: ResearchViewCatalog;
}
export const decodeResearch = decoder<ResearchWire>(compiled);
