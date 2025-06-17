import { ISuggestionFilterRequest } from "@vbkg/types";
import { useCallback, useState } from "react";

// Bulk delete suggestions

// =============================================
// UTILITY HOOKS
// =============================================

// Custom hook for managing suggestion filters with URL sync
export const useSuggestionFilters = () => {
  const [filters, setFilters] = useState<ISuggestionFilterRequest>({
    limit: 50,
    skip: 0,
  });
  
  const updateFilter = useCallback((key: keyof ISuggestionFilterRequest, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      skip: key !== 'skip' ? 0 : value, // Reset pagination when other filters change
    }));
  }, []);
  
  const resetFilters = useCallback(() => {
    setFilters({
      limit: 50,
      skip: 0,
    });
  }, []);
  
  return {
    filters,
    updateFilter,
    resetFilters,
    setFilters,
  };
};

// Custom hook for managing bulk selection
export const useBulkSuggestionSelection = () => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  const selectSuggestion = useCallback((id: string) => {
    setSelectedIds(prev => [...prev, id]);
  }, []);
  
  const deselectSuggestion = useCallback((id: string) => {
    setSelectedIds(prev => prev.filter(selectedId => selectedId !== id));
  }, []);
  
  const toggleSuggestion = useCallback((id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  }, []);
  
  const selectAll = useCallback((ids: string[]) => {
    setSelectedIds(ids);
  }, []);
  
  const clearSelection = useCallback(() => {
    setSelectedIds([]);
  }, []);
  
  const isSelected = useCallback((id: string) => {
    return selectedIds.includes(id);
  }, [selectedIds]);
  
  return {
    selectedIds,
    selectSuggestion,
    deselectSuggestion,
    toggleSuggestion,
    selectAll,
    clearSelection,
    isSelected,
    hasSelection: selectedIds.length > 0,
    selectionCount: selectedIds.length,
  };
};
