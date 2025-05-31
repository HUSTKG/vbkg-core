import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import React from "react";
import { cn } from "../../lib/utils";

export interface EntityProperty {
  key: string;
  value: string | number | boolean;
  type?: string;
}

export interface EntityRelation {
  type: string;
  target: string;
  targetType: string;
  targetId?: string;
}

export interface EntityCardProps {
  id: string | number;
  name: string;
  type: string;
  source?: string;
  description?: string;
  properties: EntityProperty[];
  relations?: EntityRelation[];
  className?: string;
  onPropertyClick?: (property: EntityProperty) => void;
  onRelationClick?: (relation: EntityRelation) => void;
  onViewDetails?: (id: string | number) => void;
  selectedProperties?: string[];
  isSelectable?: boolean;
}

const EntityCard: React.FC<EntityCardProps> = ({
  id,
  name,
  type,
  source,
  description,
  properties,
  relations = [],
  className,
  onPropertyClick,
  onRelationClick,
  onViewDetails,
  selectedProperties = [],
  isSelectable = false,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const toggleExpand = () => {
    setExpanded(!expanded);
  };

  return (
    <div
      className={cn(
        "border rounded-lg overflow-hidden bg-white dark:bg-gray-800",
        className,
      )}
    >
      <div className="p-4 bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600">
        <div className="flex justify-between items-start">
          <div>
            <div className="inline-block px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 mb-2">
              {type}
            </div>
            <h3 className="font-medium text-gray-900 dark:text-white">
              {name}
            </h3>
            {source && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Nguồn: {source}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(id)}
                className="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
                aria-label="View details"
              >
                <ExternalLink size={16} />
              </button>
            )}
            <button
              onClick={toggleExpand}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              aria-label={expanded ? "Collapse details" : "Expand details"}
              aria-expanded={expanded}
            >
              {expanded ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
            </button>
          </div>
        </div>
        {description && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
            {description}
          </p>
        )}
      </div>

      <div className="p-4">
        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
          Properties
        </h4>
        <div className="overflow-hidden">
          <table className="w-full text-sm">
            <tbody>
              {properties.map((property) => {
                const isSelected = selectedProperties.includes(property.key);
                return (
                  <tr
                    key={property.key}
                    className={cn(
                      "border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700",
                      isSelectable && "cursor-pointer",
                      isSelectable &&
                        isSelected &&
                        "bg-blue-50 dark:bg-blue-900/30",
                    )}
                    onClick={() =>
                      isSelectable &&
                      onPropertyClick &&
                      onPropertyClick(property)
                    }
                  >
                    <td className="py-2 font-medium text-gray-700 dark:text-gray-300">
                      {property.key}
                    </td>
                    <td className="py-2 text-right text-gray-900 dark:text-white">
                      {typeof property.value === "boolean"
                        ? property.value
                          ? "Yes"
                          : "No"
                        : String(property.value)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {relations.length > 0 && (expanded || relations.length <= 3) && (
          <>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 mt-4">
              Relations
            </h4>
            <ul className="space-y-2">
              {relations.map((relation, index) => (
                <li
                  key={index}
                  className={cn(
                    "flex items-center space-x-2 text-sm p-2 rounded-md",
                    onRelationClick
                      ? "hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                      : "",
                  )}
                  onClick={() => onRelationClick && onRelationClick(relation)}
                >
                  <span className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300">
                    {relation.type}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">→</span>
                  <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                    {relation.targetType}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {relation.target}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}

        {relations.length > 3 && !expanded && (
          <button
            onClick={toggleExpand}
            className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center"
          >
            <ChevronDown size={14} className="mr-1" />
            Show {relations.length} relations
          </button>
        )}
      </div>
    </div>
  );
};

export default EntityCard;
