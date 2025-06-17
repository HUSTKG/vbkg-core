import {
	useMutation,
	UseMutationOptions,
	useQueryClient,
} from "@tanstack/react-query";
import {
	ICreateOntologyClassRequest,
	ICreateOntologyClassResponse,
	IUpdateOntologyClassRequest,
	IUpdateOntologyClassResponse,
	IDeleteOntologyClassRequest,
	IDeleteOntologyClassResponse,
	ICreateOntologyPropertyRequest,
	ICreateOntologyPropertyResponse,
	IUpdateOntologyPropertyRequest,
	IUpdateOntologyPropertyResponse,
	IDeleteOntologyPropertyRequest,
	IDeleteOntologyPropertyResponse,
	IImportOntologyRequest,
	IImportOntologyResponse,
	ICreateEntityMappingRequest,
	ICreateEntityMappingResponse,
	IDeleteEntityMappingRequest,
	IDeleteEntityMappingResponse,
	IVerifyEntityMappingRequest,
	IVerifyEntityMappingResponse,
	ICreateRelationshipMappingRequest,
	IDeleteRelationshipMappingRequest,
	IDeleteRelationshipMappingResponse,
	IVerifyRelationshipMappingRequest,
	IVerifyRelationshipMappingResponse,
} from "@vbkg/types";
import { OntologyService } from "../../services/ontology";

export const useCreateOntologyClass = (
	options?: UseMutationOptions<
		ICreateOntologyClassResponse,
		Error,
		ICreateOntologyClassRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.createOntologyClass,
		...options,
	});
};

export const useUpdateOntologyClass = (
	options?: UseMutationOptions<
		IUpdateOntologyClassResponse,
		Error,
		IUpdateOntologyClassRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.updateOntologyClass,
		...options,
	});
};

export const useDeleteOntologyClass = (
	options?: UseMutationOptions<
		IDeleteOntologyClassResponse,
		Error,
		IDeleteOntologyClassRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.deleteOntologyClass,
		...options,
	});
};

// FIBO Property Mutation Hooks (keeping existing)
export const useCreateOntologyProperty = (
	options?: UseMutationOptions<
		ICreateOntologyPropertyResponse,
		Error,
		ICreateOntologyPropertyRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.createOntologyProperty,
		...options,
	});
};

export const useUpdateOntologyProperty = (
	options?: UseMutationOptions<
		IUpdateOntologyPropertyResponse,
		Error,
		IUpdateOntologyPropertyRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.updateOntologyProperty,
		...options,
	});
};

export const useDeleteOntologyProperty = (
	options?: UseMutationOptions<
		IDeleteOntologyPropertyResponse,
		Error,
		IDeleteOntologyPropertyRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.deleteOntologyProperty,
		...options,
	});
};

// Ontology Import Hook (keeping existing)
export const useImportOntology = (
	options?: UseMutationOptions<
		IImportOntologyResponse,
		Error,
		IImportOntologyRequest
	>,
) => {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: OntologyService.importOntology,
		...options,
		onSuccess: (...params) => {
			// Invalidate queries related to FIBO classes and properties
			queryClient.invalidateQueries({queryKey: ["ontologyClasses", {}]});
			queryClient.invalidateQueries({queryKey: ["ontologyProperties", {}]});
			options?.onSuccess?.(...params);
		},
	});
};

// Entity Mapping Mutation Hooks (updated)
export const useCreateEntityMapping = (
	options?: UseMutationOptions<
		ICreateEntityMappingResponse,
		Error,
		ICreateEntityMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.createEntityMapping,
		...options,
	});
};

export const useDeleteEntityMapping = (
	options?: UseMutationOptions<
		IDeleteEntityMappingResponse,
		Error,
		IDeleteEntityMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.deleteEntityMapping,
		...options,
	});
};

export const useVerifyEntityMapping = (
	options?: UseMutationOptions<
		IVerifyEntityMappingResponse,
		Error,
		IVerifyEntityMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.verifyEntityMapping,
		...options,
	});
};

// Relationship Mapping Mutation Hooks (updated)
export const useCreateRelationshipMapping = (
	options?: UseMutationOptions<
		any,
		Error,
		ICreateRelationshipMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.createRelationshipMapping,
		...options,
	});
};

export const useDeleteRelationshipMapping = (
	options?: UseMutationOptions<
		IDeleteRelationshipMappingResponse,
		Error,
		IDeleteRelationshipMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.deleteRelationshipMapping,
		...options,
	});
};

export const useVerifyRelationshipMapping = (
	options?: UseMutationOptions<
		IVerifyRelationshipMappingResponse,
		Error,
		IVerifyRelationshipMappingRequest
	>,
) => {
	return useMutation({
		mutationFn: OntologyService.verifyRelationshipMapping,
		...options,
	});
};

// Bulk Operation Hooks
// export const useBulkCreateEntityMappings = (
//   options?: UseMutationOptions<
//     IBulkCreateEntityMappingsResponse,
//     Error,
//     IBulkCreateEntityMappingsRequest
//   >,
// ) => {
//   return useMutation({
//     mutationFn: OntologyService.bulkCreateEntityMappings,
//     ...options,
//   });
// };
//
// export const useBulkCreateRelationshipMappings = (
//   options?: UseMutationOptions<
//     IBulkCreateRelationshipMappingsResponse,
//     Error,
//     IBulkCreateRelationshipMappingsRequest
//   >,
// ) => {
//   return useMutation({
//     mutationFn: OntologyService.bulkCreateRelationshipMappings,
//     ...options,
//   });
// };
