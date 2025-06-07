import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, X, Check } from 'lucide-react';

// Types definition
export interface Option {
  value: string;
  label: string;
}

interface SearchSelectProps {
  options?: Option[];
  placeholder?: string;
  multiple?: boolean;
  value?: Option | Option[] | null;
  onChange?: (value: Option | Option[] | null) => void;
  className?: string;
  disabled?: boolean;
  clearable?: boolean;
  // Search control props
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
  loading?: boolean;
  loadingText?: string;
  noResultsText?: string;
}

const SearchSelect: React.FC<SearchSelectProps> = ({
  options = [],
  placeholder = "Tìm kiếm và chọn...",
  multiple = false,
  value,
  onChange,
  className = "",
  disabled = false,
  clearable = true,
  searchTerm,
  onSearchChange,
  loading = false,
  loadingText = "Đang tải...",
  noResultsText = "Không tìm thấy kết quả"
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [internalSearchTerm, setInternalSearchTerm] = useState<string>('');
  const [internalValue, setInternalValue] = useState<Option | Option[] | null>(
    multiple ? [] : null
  );
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Use controlled or uncontrolled search term
  const currentSearchTerm = searchTerm !== undefined ? searchTerm : internalSearchTerm;
  const setCurrentSearchTerm = (term: string) => {
    if (searchTerm === undefined) {
      setInternalSearchTerm(term);
    }
    if (onSearchChange) {
      onSearchChange(term);
    }
  };

  // Use controlled or uncontrolled value
  const currentValue = value !== undefined ? value : internalValue;
  const setCurrentValue = (newValue: Option | Option[] | null) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    if (onChange) {
      onChange(newValue);
    }
  };

  // When using controlled search, don't filter options here (API will handle it)
  // When using uncontrolled search, filter locally
  const filteredOptions = onSearchChange 
    ? options // API handles filtering
    : options.filter(option =>
        option.label.toLowerCase().includes(currentSearchTerm.toLowerCase())
      );

  // Helper functions for type checking
  const isMultipleValue = (val: Option | Option[] | null): val is Option[] => {
    return multiple && Array.isArray(val);
  };

  const isSingleValue = (val: Option | Option[] | null): val is Option => {
    return !multiple && val !== null && !Array.isArray(val);
  };

  // Handle option selection
  const handleSelectOption = (option: Option) => {
    if (multiple) {
      const currentArray = isMultipleValue(currentValue) ? currentValue : [];
      const isSelected = currentArray.some(selected => selected.value === option.value);
      
      let newValue: Option[];
      if (isSelected) {
        newValue = currentArray.filter(selected => selected.value !== option.value);
      } else {
        newValue = [...currentArray, option];
      }
      
      setCurrentValue(newValue);
    } else {
      setCurrentValue(option);
      setCurrentSearchTerm('');
      setIsOpen(false);
    }
  };

  // Handle clear selection
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentValue(multiple ? [] : null);
    setCurrentSearchTerm('');
  };

  // Remove single option from multiple selection
  const removeOption = (optionToRemove: Option, e: React.MouseEvent) => {
    e.stopPropagation();
    if (isMultipleValue(currentValue)) {
      const newValue = currentValue.filter(option => option.value !== optionToRemove.value);
      setCurrentValue(newValue);
    }
  };

  // Check if option is selected
  const isOptionSelected = (option: Option): boolean => {
    if (multiple && isMultipleValue(currentValue)) {
      return currentValue.some(selected => selected.value === option.value);
    }
    if (!multiple && isSingleValue(currentValue)) {
      return currentValue.value === option.value;
    }
    return false;
  };

  // Get display value
  const getDisplayValue = (): React.ReactNode => {
    if (multiple && isMultipleValue(currentValue)) {
      if (currentValue.length === 0) {
        return <span className="text-gray-500">{placeholder}</span>;
      }
      return (
        <div className="flex items-center flex-wrap gap-1">
          {currentValue.map((option) => (
            <span
              key={option.value}
              className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-md"
            >
              {option.label}
              <button
                onClick={(e) => removeOption(option, e)}
                className="ml-1 hover:bg-blue-200 rounded"
                disabled={disabled}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      );
    }
    
    if (!multiple && isSingleValue(currentValue)) {
      return <span className="text-gray-900">{currentValue.label}</span>;
    }
    
    return <span className="text-gray-500">{placeholder}</span>;
  };

  // Has value check
  const hasValue = (): boolean => {
    if (multiple && isMultipleValue(currentValue)) {
      return currentValue.length > 0;
    }
    return !multiple && currentValue !== null;
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    
    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        setIsOpen(!isOpen);
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div className={`relative w-full ${className}`} ref={dropdownRef}>
      <div
        className={`relative h-9 flex items-center px-3 py-2 border rounded-md bg-white cursor-pointer transition-colors ${
          disabled
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-gray-400 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500'
        }`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
      >
        <Search className="w-4 h-4 text-gray-400 mr-2" />
        
        <div className="flex-1 min-w-0">
          {!hasValue() && !multiple ? (
            <input
              type="text"
              placeholder={placeholder}
              value={currentSearchTerm}
              onChange={(e) => setCurrentSearchTerm(e.target.value)}
              onFocus={() => !disabled && setIsOpen(true)}
              className="w-full outline-none bg-transparent text-gray-900 placeholder-gray-500"
              disabled={disabled}
            />
          ) : (
            getDisplayValue()
          )}
        </div>
        
        {clearable && hasValue() && !disabled && (
          <button
            onClick={handleClear}
            className="p-1 hover:bg-gray-100 rounded mr-1"
            title="Xóa"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
        
        <ChevronDown 
          className={`w-4 h-4 text-gray-400 transition-transform ${
            isOpen ? 'rotate-180' : ''
          } ${disabled ? 'opacity-50' : ''}`} 
        />
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {/* Search input in dropdown */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm kiếm..."
                value={currentSearchTerm}
                onChange={(e) => setCurrentSearchTerm(e.target.value)}
                className="w-full h-10 pl-10 pr-3 py-2 border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                autoFocus
              />
            </div>
          </div>
          
          {/* Options list */}
          <div className="max-h-48 overflow-y-auto">
            {loading ? (
              <div className="px-3 py-2 text-gray-500 flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                {loadingText}
              </div>
            ) : filteredOptions.length > 0 ? (
              filteredOptions.map((option) => {
                const isSelected = isOptionSelected(option);
                return (
                  <div
                    key={option.value}
                    onClick={() => handleSelectOption(option)}
                    className={`px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center justify-between ${
                      isSelected ? 'bg-blue-50' : ''
                    }`}
                  >
                    <span className="text-gray-900">{option.label}</span>
                    {isSelected && <Check className="w-4 h-4 text-blue-500" />}
                  </div>
                );
              })
            ) : (
              <div className="px-3 py-2 text-gray-500">{noResultsText}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchSelect;
