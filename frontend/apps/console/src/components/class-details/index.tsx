import React, { useState, useEffect } from 'react';
import { Edit2, Save, X, Plus, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface OntologyProperty {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

export interface OntologyClass {
  id: string | number;
  name: string;
  description: string;
  properties: OntologyProperty[];
}

export interface ClassDetailsProps {
  classItem: OntologyClass | null;
  onUpdate?: (updatedClass: OntologyClass) => void;
  onCancel?: () => void;
  onDelete?: (id: string | number) => void;
  readOnly?: boolean;
  className?: string;
}

// Available property types
const PROPERTY_TYPES = [
  'string',
  'number',
  'boolean',
  'date',
  'object',
  'array',
  'reference',
  'enum',
  'url',
  'email',
];

const ClassDetails: React.FC<ClassDetailsProps> = ({
  classItem,
  onUpdate,
  onCancel,
  onDelete,
  readOnly = false,
  className,
}) => {
  const [editMode, setEditMode] = useState(false);
  const [editedClass, setEditedClass] = useState<OntologyClass | null>(classItem);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Update local state when classItem changes
  useEffect(() => {
    setEditedClass(classItem);
    setEditMode(false);
    setValidationErrors({});
    setHasUnsavedChanges(false);
  }, [classItem]);

  if (!classItem) {
    return (
      <div className={cn(
        "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6",
        className
      )}>
        <div className="py-8 text-center text-gray-500 dark:text-gray-400">
          Chọn một class từ danh sách để xem chi tiết
        </div>
      </div>
    );
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    setEditedClass(prev => {
      if (!prev) return null;
      return {
        ...prev,
        [name]: value
      };
    });
    
    setHasUnsavedChanges(true);
    
    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handlePropertyChange = (index: number, field: keyof OntologyProperty, value: string | boolean) => {
    if (!editedClass) return;

    const updatedProperties = [...editedClass.properties];
    updatedProperties[index] = {
      ...updatedProperties[index],
      [field]: value
    };
    
    setEditedClass({
      ...editedClass,
      properties: updatedProperties
    });
    
    setHasUnsavedChanges(true);
    
    // Clear validation error for this property
    const errorKey = `property-${index}-${field}`;
    if (validationErrors[errorKey]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  const handleAddProperty = () => {
    if (!editedClass) return;
    
    setEditedClass({
      ...editedClass,
      properties: [
        ...editedClass.properties,
        { name: '', type: 'string', required: false, description: '' }
      ]
    });
    
    setHasUnsavedChanges(true);
  };

  const handleRemoveProperty = (index: number) => {
    if (!editedClass) return;
    
    setEditedClass({
      ...editedClass,
      properties: editedClass.properties.filter((_, i) => i !== index)
    });
    
    setHasUnsavedChanges(true);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!editedClass) return false;
    
    // Validate class name
    if (!editedClass.name.trim()) {
      errors.name = 'Tên class không được để trống';
    }
    
    // Validate properties
    editedClass.properties.forEach((prop, index) => {
      if (!prop.name.trim()) {
        errors[`property-${index}-name`] = 'Tên property không được để trống';
      }
      
      // Check for duplicate property names
      const duplicateName = editedClass.properties.findIndex(
        (p, i) => p.name === prop.name && i !== index
      );
      
      if (duplicateName !== -1 && prop.name.trim()) {
        errors[`property-${index}-name`] = 'Tên property không được trùng lặp';
      }
    });
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = () => {
    if (!editedClass) return;
    
    if (validateForm()) {
      if (onUpdate) {
        onUpdate(editedClass);
      }
      setEditMode(false);
      setHasUnsavedChanges(false);
    }
  };

  const handleCancel = () => {
    setEditedClass(classItem);
    setEditMode(false);
    setValidationErrors({});
    setHasUnsavedChanges(false);
    
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <div className={cn(
      "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden",
      className
    )}>
      <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Chi tiết class</h3>
        <div className="flex space-x-2">
          {hasUnsavedChanges && editMode && (
            <div className="flex items-center text-amber-500 dark:text-amber-400 text-sm mr-2">
              <AlertCircle size={14} className="mr-1" />
              Chưa lưu thay đổi
            </div>
          )}
          
          {!readOnly && (editMode ? (
            <>
              <button
                onClick={handleSave}
                className="p-1.5 bg-green-100 text-green-600 rounded-md hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50"
                aria-label="Save changes"
              >
                <Save size={16} />
              </button>
              <button
                onClick={handleCancel}
                className="p-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600"
                aria-label="Cancel editing"
              >
                <X size={16} />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditMode(true)}
                className="p-1.5 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
                aria-label="Edit class"
              >
                <Edit2 size={16} />
              </button>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="p-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600"
                  aria-label="Close details"
                >
                  <X size={16} />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => {
                    if (window.confirm(`Bạn có chắc chắn muốn xóa class "${classItem.name}"?`)) {
                      onDelete(classItem.id);
                    }
                  }}
                  className="p-1.5 bg-red-100 text-red-600 rounded-md hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
                  aria-label="Delete class"
                >
                  <Trash2 size={16} />
                </button>
              )}
            </>
          ))}
        </div>
      </div>
      
      <div className="p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Tên class
          </label>
          {editMode ? (
            <div>
              <input
                type="text"
                name="name"
                value={editedClass?.name || ''}
                onChange={handleChange}
                className={cn(
                  "w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white",
                  validationErrors.name && "border-red-500 dark:border-red-500"
                )}
              />
              {validationErrors.name && (
                <p className="mt-1 text-sm text-red-500">{validationErrors.name}</p>
              )}
            </div>
          ) : (
            <p className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md text-gray-900 dark:text-white">
              {classItem.name}
            </p>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Mô tả
          </label>
          {editMode ? (
            <textarea
              name="description"
              value={editedClass?.description || ''}
              onChange={handleChange}
              rows={3}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          ) : (
            <p className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md text-gray-900 dark:text-white">
              {classItem.description || <span className="text-gray-400 dark:text-gray-500 italic">Không có mô tả</span>}
            </p>
          )}
        </div>
        
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Properties
            </label>
            {editMode && (
              <button
                onClick={handleAddProperty}
                className="p-1 flex items-center text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
              >
                <Plus size={12} className="mr-1" />
                Thêm property
              </button>
            )}
          </div>
          
          <div className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Tên
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Kiểu dữ liệu
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Bắt buộc
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Mô tả
                  </th>
                  {editMode && (
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Hành động
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {editedClass?.properties.length ? (
                  editedClass.properties.map((prop, index) => (
                    <tr key={index}>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {editMode ? (
                          <div>
                            <input
                              type="text"
                              value={prop.name}
                              onChange={(e) => handlePropertyChange(index, 'name', e.target.value)}
                              className={cn(
                                "w-full p-1 border border-gray-300 dark:border-gray-600 rounded-sm dark:bg-gray-700 text-gray-900 dark:text-white",
                                validationErrors[`property-${index}-name`] && "border-red-500 dark:border-red-500"
                              )}
                            />
                            {validationErrors[`property-${index}-name`] && (
                              <p className="mt-0.5 text-xs text-red-500">
                                {validationErrors[`property-${index}-name`]}
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-900 dark:text-white">{prop.name}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {editMode ? (
                          <select
                            value={prop.type}
                            onChange={(e) => handlePropertyChange(index, 'type', e.target.value)}
                            className="w-full p-1 border border-gray-300 dark:border-gray-600 rounded-sm dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            {PROPERTY_TYPES.map(type => (
                              <option key={type} value={type}>{type}</option>
                            ))}
                          </select>
                        ) : (
                          <span className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                            {prop.type}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {editMode ? (
                          <input
                            type="checkbox"
                            checked={prop.required}
                            onChange={(e) => handlePropertyChange(index, 'required', e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        ) : (
                          <span className="text-gray-900 dark:text-white">
                            {prop.required ? (
                              <CheckCircle size={16} className="text-green-500" />
                            ) : (
                              <X size={16} className="text-gray-400" />
                            )}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {editMode ? (
                          <input
                            type="text"
                            value={prop.description}
                            onChange={(e) => handlePropertyChange(index, 'description', e.target.value)}
                            className="w-full p-1 border border-gray-300 dark:border-gray-600 rounded-sm dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        ) : (
                          <span className="text-gray-900 dark:text-white">
                            {prop.description || <span className="text-gray-400 dark:text-gray-500 italic">-</span>}
                          </span>
                        )}
                      </td>
                      {editMode && (
                        <td className="px-3 py-2 whitespace-nowrap text-right">
                          <button
                            onClick={() => handleRemoveProperty(index)}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 p-1"
                            aria-label="Remove property"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={editMode ? 5 : 4} className="px-3 py-4 text-center text-gray-500 dark:text-gray-400">
                      Không có property nào
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClassDetails;
