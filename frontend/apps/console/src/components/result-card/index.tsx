import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, Copy, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface ResultProperty {
  key: string;
  value: string | number | boolean;
}

export interface ResultRelation {
  type: string;
  target: string;
  targetType: string;
  targetId?: string;
}

export interface ResultCardProps {
  id: string | number;
  type: string;
  name: string;
  properties: Record<string, any> | ResultProperty[];
  relations?: ResultRelation[];
  className?: string;
  onViewDetails?: (id: string | number) => void;
  onRelationClick?: (relation: ResultRelation) => void;
  highlightTerms?: string[];
}

const ResultCard: React.FC<ResultCardProps> = ({
  id,
  type,
  name,
  properties,
  relations = [],
  className,
  onViewDetails,
  onRelationClick,
  highlightTerms = [],
}) => {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Convert properties object to array if it's not already
  const propertiesArray = Array.isArray(properties) 
    ? properties 
    : Object.entries(properties).map(([key, value]) => ({ key, value }));

  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  const copyToClipboard = () => {
    const textToCopy = `
      ID: ${id}
      Type: ${type}
      Name: ${name}
      Properties: ${propertiesArray.map(p => `${p.key}: ${p.value}`).join(', ')}
      Relations: ${relations.map(r => `${r.type} → ${r.target} (${r.targetType})`).join(', ')}
    `;
    
    navigator.clipboard.writeText(textToCopy.trim())
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
  };

  // Function to highlight text
  const highlightText = (text: string) => {
    if (highlightTerms.length === 0) return text;
    
    const regex = new RegExp(`(${highlightTerms.join('|')})`, 'gi');
    const parts = text.toString().split(regex);
    
    return (
      <>
        {parts.map((part, i) => (
          regex.test(part) ? 
            <mark key={i} className="bg-yellow-200 dark:bg-yellow-700">{part}</mark> : 
            part
        ))}
      </>
    );
  };

  return (
    <div 
      className={cn(
        "bg-white dark:bg-gray-800 rounded-lg shadow",
        className
      )}
    >
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-start">
          <div>
            <div className="inline-block px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 mb-2">
              {highlightText(type)}
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {highlightText(name)}
            </h3>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={copyToClipboard}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Copy result details"
              title="Copy to clipboard"
            >
              {copied ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
            </button>
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(id)}
                className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="View details"
                title="View details"
              >
                <ExternalLink size={16} />
              </button>
            )}
            <button
              onClick={toggleExpanded}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label={expanded ? "Collapse details" : "Expand details"}
              aria-expanded={expanded}
              title={expanded ? "Collapse" : "Expand"}
            >
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
          Properties
        </h4>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {propertiesArray.map((prop) => (
            <div key={prop.key} className="bg-gray-50 dark:bg-gray-700 p-2 rounded">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 block">
                {prop.key}
              </span>
              <span className="text-sm text-gray-900 dark:text-white">
                {typeof prop.value === 'boolean' 
                  ? (prop.value ? 'Yes' : 'No')
                  : highlightText(String(prop.value))
                }
              </span>
            </div>
          ))}
        </div>
        
        {expanded && relations.length > 0 && (
          <>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Relations
            </h4>
            <ul className="space-y-2">
              {relations.map((relation, index) => (
                <li 
                  key={index} 
                  className={cn(
                    "flex items-center space-x-2 text-sm p-2 rounded-md",
                    onRelationClick ? "hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer" : ""
                  )}
                  onClick={() => onRelationClick && onRelationClick(relation)}
                >
                  <span className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300">
                    {highlightText(relation.type)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">→</span>
                  <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                    {relation.targetType}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {highlightText(relation.target)}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
        
        {!expanded && relations.length > 0 && (
          <button
            onClick={toggleExpanded}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center"
          >
            <ChevronDown size={14} className="mr-1" />
            Show {relations.length} relations
          </button>
        )}
      </div>
    </div>
  );
};

export default ResultCard;
