import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Play,
  RefreshCw,
  Calendar,
  ArrowUpDown,
  FileText,
  Zap,
  ChevronDown,
  ChevronUp,
  GitMerge,
  Lightbulb,
  Copy,
  Check,
} from "lucide-react";
import {
  useAutoResolveConflict,
  useConflicts,
  useDetectConflicts,
  useResolveConflict,
} from "@vbkg/api-client";
import { ConflictStatus, ConflictType } from "@vbkg/types";
import {
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@vbkg/ui";

// Reusable Components
const StatusBadge = ({ status }: any) => {
  const statusConfig: any = {
    detected: {
      label: "Phát hiện",
      color:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
    },
    under_review: {
      label: "Đang xem xét",
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    },
    resolved_manual: {
      label: "Đã giải quyết",
      color:
        "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
    },
    resolved_auto: {
      label: "Tự động giải quyết",
      color:
        "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
    },
    rejected: {
      label: "Từ chối",
      color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
    },
    escalated: {
      label: "Báo cáo",
      color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
    },
  };

  const config = statusConfig[status] || statusConfig.detected;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  );
};

const SeverityBadge = ({ severity }: any) => {
  const severityConfig: any = {
    low: {
      label: "Thấp",
      color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
    },
    medium: {
      label: "Trung bình",
      color:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
    },
    high: {
      label: "Cao",
      color:
        "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
    },
    critical: {
      label: "Nghiêm trọng",
      color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
    },
  };

  const config = severityConfig[severity] || severityConfig.medium;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  );
};

const ConflictTypeIcon = ({ type }: any) => {
  const iconMap: any = {
    duplicate_entity: <GitMerge className="h-4 w-4 text-purple-500" />,
    attribute_mismatch: <FileText className="h-4 w-4 text-blue-500" />,
    contradictory_relationship: (
      <ArrowUpDown className="h-4 w-4 text-red-500" />
    ),
    temporal_conflict: <Calendar className="h-4 w-4 text-orange-500" />,
    source_conflict: <RefreshCw className="h-4 w-4 text-indigo-500" />,
    schema_mismatch: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
    missing_relationship: <XCircle className="h-4 w-4 text-gray-500" />,
  };

  return iconMap[type] || <AlertTriangle className="h-4 w-4 text-gray-500" />;
};

const ResolutionMethodBadge = ({ method }: any) => {
  const colors: any = {
    merge_entities:
      "bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400",
    keep_both:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400",
    keep_source:
      "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
    keep_target:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
    create_new:
      "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400",
  };

  const methodLabels: any = {
    merge_entities: "Hợp nhất",
    keep_both: "Giữ cả hai",
    keep_source: "Giữ nguồn",
    keep_target: "Giữ đích",
    create_new: "Tạo mới",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded-full ${colors[method] || "bg-gray-100 text-gray-800"}`}
    >
      {methodLabels[method] || method}
    </span>
  );
};

const EntityCard = ({ entity, label }: any) => {
  const [copied, setCopied] = useState(false);

  const handleCopyId = () => {
    navigator.clipboard.writeText(entity.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
          {label}
        </span>
        <button
          onClick={handleCopyId}
          className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex items-center"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span className="ml-1">{entity.id?.slice(0, 8)}...</span>
        </button>
      </div>
      <p className="text-sm font-medium text-gray-900 dark:text-white">
        {entity.text}
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Loại: {entity.type || "N/A"}
      </p>
    </div>
  );
};

const AISuggestionCard = ({ suggestion, index, onApply, isApplying }: any) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <ResolutionMethodBadge method={suggestion.resolution_method} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Gợi ý #{index + 1}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 rounded-full">
            {Math.round((suggestion.confidence_score || 0) * 100)}%
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      <p className="text-sm text-black dark:text-white mb-3">
        {suggestion.reasoning}
      </p>

      {isExpanded && (
        <div className="space-y-3 mb-4">
          {suggestion.potential_risks && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-md border border-yellow-200 dark:border-yellow-800">
              <h5 className="text-xs font-medium text-yellow-800 dark:text-yellow-400 mb-1 flex items-center">
                <AlertTriangle size={12} className="mr-1" />
                RỦI RO TIỀM ẨN:
              </h5>
              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                {suggestion.potential_risks}
              </p>
            </div>
          )}

          {suggestion.specific_actions && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-200 dark:border-blue-800">
              <h5 className="text-xs font-medium text-blue-800 dark:text-blue-400 mb-2 flex items-center">
                <Lightbulb size={12} className="mr-1" />
                HÀNH ĐỘNG CỤ THỂ:
              </h5>
              <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                {suggestion.specific_actions.map(
                  (action: string, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="inline-block w-1 h-1 bg-blue-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                      <span>{action}</span>
                    </li>
                  ),
                )}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={() => onApply(suggestion)}
          disabled={isApplying}
          className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isApplying ? (
            <>
              <RefreshCw size={12} className="mr-1 animate-spin" />
              Đang áp dụng...
            </>
          ) : (
            <>
              <Check size={12} className="mr-1" />
              Áp dụng gợi ý
            </>
          )}
        </button>
      </div>
    </div>
  );
};

const ConflictDetailsModal = ({
  conflict,
  isOpen,
  onClose,
  onResolve,
  onAutoResolve,
  onApplySuggestion,
}: any) => {
  const [applyingIndex, setApplyingIndex] = useState<number | null>(null);

  if (!isOpen || !conflict) return null;

  const handleApplySuggestion = async (suggestion: any, index: number) => {
    setApplyingIndex(index);
    try {
      await onApplySuggestion(conflict.id, suggestion);
    } finally {
      setApplyingIndex(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Chi tiết xung đột
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                ID: {conflict.id}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XCircle size={20} />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Loại xung đột
              </label>
              <div className="flex items-center space-x-2">
                <ConflictTypeIcon type={conflict.conflict_type} />
                <span className="text-sm text-gray-900 dark:text-white capitalize">
                  {conflict.conflict_type.replace("_", " ")}
                </span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Độ nghiêm trọng
              </label>
              <SeverityBadge severity={conflict.severity} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Trạng thái
              </label>
              <StatusBadge status={conflict.status} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Độ tin cậy
              </label>
              <span className="text-sm text-gray-900 dark:text-white">
                {Math.round(conflict.confidence_score * 100)}%
              </span>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Mô tả
            </label>
            <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
              {conflict.description}
            </p>
          </div>

          {/* Context Data - Entity Information */}
          {conflict.context_data && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Thông tin thực thể
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <EntityCard
                  entity={{
                    id: conflict.source_entity_id,
                    text: conflict.context_data.entity1_text,
                    type: conflict.context_data.entity_type,
                  }}
                  label="Thực thể nguồn"
                />
                <EntityCard
                  entity={{
                    id: conflict.target_entity_id,
                    text: conflict.context_data.entity2_text,
                    type: conflict.context_data.entity_type,
                  }}
                  label="Thực thể đích"
                />
              </div>
            </div>
          )}

          {/* Similarity Scores */}
          {conflict.context_data?.similarity_scores && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Điểm tương đồng
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(conflict.context_data.similarity_scores).map(
                  ([key, value]: [string, any]) => (
                    <div
                      key={key}
                      className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md text-center"
                    >
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {Math.round(parseFloat(value) * 100)}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                        {key === "text"
                          ? "Văn bản"
                          : key === "semantic"
                            ? "Ngữ nghĩa"
                            : key === "attributes"
                              ? "Thuộc tính"
                              : key === "exact"
                                ? "Chính xác"
                                : key}
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {/* Conflicting Attributes */}
          {conflict.conflicting_attributes && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Thuộc tính xung đột
              </label>
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                {Object.entries(conflict.conflicting_attributes).map(
                  ([key, values]) => (
                    <div key={key} className="mb-2 last:mb-0">
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        {key}:
                      </span>
                      <div className="mt-1 space-y-1">
                        {Array.isArray(values) ? (
                          values.map((value, index) => (
                            <div
                              key={index}
                              className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-2 rounded border"
                            >
                              {value}
                            </div>
                          ))
                        ) : (
                          <div className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-2 rounded border">
                            {values as any}
                          </div>
                        )}
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {/* AI Suggestions */}
          {conflict.auto_resolution_suggestions &&
            conflict.auto_resolution_suggestions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Gợi ý giải quyết từ AI
                </label>
                <div className="space-y-4">
                  {conflict.auto_resolution_suggestions.map(
                    (suggestion: any, index: number) => (
                      <AISuggestionCard
                        key={index}
                        suggestion={suggestion}
                        index={index}
                        onApply={(suggestion: any) =>
                          handleApplySuggestion(suggestion, index)
                        }
                        isApplying={applyingIndex === index}
                      />
                    ),
                  )}
                </div>
              </div>
            )}

          {/* Detection Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Phát hiện bởi
              </label>
              <span className="text-sm text-gray-900 dark:text-white">
                {conflict.detected_by}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Thời gian phát hiện
              </label>
              <span className="text-sm text-gray-900 dark:text-white">
                {new Date(conflict.detected_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Assignment Info */}
          {conflict.assigned_to && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Được giao cho
              </label>
              <span className="text-sm text-gray-900 dark:text-white">
                {conflict.assigned_to}
              </span>
            </div>
          )}

          {/* Resolution Info */}
          {conflict.resolution && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Thông tin giải quyết
              </label>
              <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-md">
                <p className="text-sm text-gray-900 dark:text-white">
                  <strong>Phương pháp:</strong>{" "}
                  {conflict.resolution.resolution_method}
                </p>
                {conflict.resolution.reasoning && (
                  <p className="text-sm text-gray-900 dark:text-white mt-1">
                    <strong>Lý do:</strong> {conflict.resolution.reasoning}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            Đóng
          </button>
          {conflict.status === "detected" && (
            <>
              <button
                onClick={() => onAutoResolve(conflict.id)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
              >
                <Zap size={14} className="mr-1" />
                Tự động giải quyết
              </button>
              <button
                onClick={() => onResolve(conflict.id)}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 flex items-center"
              >
                <CheckCircle size={14} className="mr-1" />
                Giải quyết thủ công
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const ConflictsPage = () => {
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  const { data: conflictsResponse, isFetching: loading } = useConflicts({
    limit: 50,
    status:
      statusFilter !== "all" ? (statusFilter as ConflictStatus) : undefined,
    conflict_type:
      typeFilter !== "all" ? (typeFilter as ConflictType) : undefined,
  });

  const conflicts = conflictsResponse?.data;

  const { mutate: detectConflict, isPending: isDetecting } =
    useDetectConflicts();
  const { mutate: resolveConflict } = useResolveConflict();
  const { mutate: autoResolveConflict } = useAutoResolveConflict();

  const handleDetectConflicts = async () => {
    detectConflict();
  };

  const handleViewDetails = (conflict: any) => {
    setSelectedConflict(conflict);
    setShowDetails(true);
  };

  const handleResolveConflict = async (conflictId: string) => {
    setShowDetails(false);
    alert("Xung đột đã được đánh dấu là đã giải quyết");
  };

  const handleAutoResolve = async (conflictId: any) => {
    autoResolveConflict({ conflict_id: conflictId, confidence_threshold: 0.8 });
    setShowDetails(false);
  };

  const handleApplySuggestion = async (conflictId: string, suggestion: any) => {
    // Apply specific AI suggestion
    try {
      resolveConflict({
        conflict_id: conflictId,
        resolution: {
          resolution_method: suggestion.resolution_method,
          reasoning: suggestion.reasoning,
          confidence_score: suggestion.confidence_score,
          resolution_data: suggestion.specific_actions || {},
        },
      });
      setShowDetails(false);
      alert("Đã áp dụng gợi ý AI thành công!");
    } catch (error) {
      alert("Có lỗi xảy ra khi áp dụng gợi ý AI");
    }
  };

  const getStatusStats = () => {
    const stats = {
      total: conflictsResponse?.meta.total || 0,
      detected: conflicts?.filter((c) => c.status === "detected").length || 0,
      under_review:
        conflicts?.filter((c) => c.status === "under_review").length || 0,
      resolved:
        conflicts?.filter((c) => c.status.includes("resolved")).length || 0,
      escalated: conflicts?.filter((c) => c.status === "escalated").length || 0,
    };
    return stats;
  };

  const stats = getStatusStats();

  // Filter conflicts based on search term
  const filteredConflicts = conflicts?.filter((conflict) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      conflict.id.toLowerCase().includes(searchLower) ||
      conflict.description.toLowerCase().includes(searchLower) ||
      conflict.context_data?.entity1_text
        ?.toLowerCase()
        .includes(searchLower) ||
      conflict.context_data?.entity2_text?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Quản lý xung đột
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Phát hiện và giải quyết các xung đột trong Knowledge Graph
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleDetectConflicts}
                disabled={isDetecting}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Play className="h-4 w-4 mr-2" />
                {isDetecting ? "Đang phát hiện..." : "Phát hiện xung đột"}
              </button>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Tổng số xung đột
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {stats.detected}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Mới phát hiện
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">
              {stats.under_review}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Đang xem xét
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">
              {stats.resolved}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Đã giải quyết
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-red-600">
              {stats.escalated}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Đã báo cáo
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tìm kiếm
              </label>
              <div className="relative">
                <Input
                  type="text"
                  placeholder="Tìm theo ID, mô tả hoặc entity..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Trạng thái
              </label>
              <Select
                value={statusFilter}
                onValueChange={(value: string) => setStatusFilter(value)}
              >
                <SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
                  Chọn trạng thái
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="detected">Phát hiện</SelectItem>
                  <SelectItem value="under_review">Đang xem xét</SelectItem>
                  <SelectItem value="resolved_manual">Đã giải quyết</SelectItem>
                  <SelectItem value="escalated">Đã báo cáo</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Độ nghiêm trọng
              </label>
              <Select
                defaultValue={statusFilter}
                onValueChange={(value) => setSeverityFilter(value)}
              >
                <SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
                  Chọn độ nghiêm trọng
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="detected">Thấp</SelectItem>
                  <SelectItem value="under_review">Trung bình</SelectItem>
                  <SelectItem value="resolved_manual">Cao</SelectItem>
                  <SelectItem value="escalated">Nghiêm trọng</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Loại xung đột
              </label>
              <Select
                value={typeFilter}
                onValueChange={(e) => setTypeFilter(e)}
              >
                <SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
                  Chọn loại xung đột
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="duplicate_entity">
                    Entity trùng lặp
                  </SelectItem>
                  <SelectItem value="attribute_mismatch">
                    Thuộc tính không khớp
                  </SelectItem>
                  <SelectItem value="contradictory_relationship">
                    Quan hệ mâu thuẫn
                  </SelectItem>
                  <SelectItem value="temporal_conflict">
                    Xung đột về thời gian
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Conflicts List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Danh sách xung đột ({filteredConflicts?.length || 0})
            </h3>
          </div>

          {!filteredConflicts || filteredConflicts.length === 0 ? (
            <div className="p-12 text-center">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Không có xung đột nào
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                {searchTerm ||
                statusFilter !== "all" ||
                severityFilter !== "all" ||
                typeFilter !== "all"
                  ? "Không tìm thấy xung đột nào phù hợp với bộ lọc."
                  : "Chưa phát hiện xung đột nào trong hệ thống."}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredConflicts?.map((conflict) => (
                <div
                  key={conflict.id}
                  className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <ConflictTypeIcon type={conflict.conflict_type} />
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {conflict.description}
                        </h4>
                        <StatusBadge status={conflict.status} />
                        <SeverityBadge severity={conflict.severity} />
                      </div>

                      {/* Entity information */}
                      {conflict.context_data && (
                        <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400 mb-2">
                          <span className="bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
                            {conflict.context_data.entity1_text}
                          </span>
                          <span>vs</span>
                          <span className="bg-orange-100 dark:bg-orange-900/30 px-2 py-1 rounded">
                            {conflict.context_data.entity2_text}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                        <span>ID: {conflict.id.slice(0, 8)}...</span>
                        <span>
                          Độ tin cậy:{" "}
                          {Math.round(conflict.confidence_score * 100)}%
                        </span>
                        <span>
                          Phát hiện:{" "}
                          {new Date(conflict.detected_at).toLocaleDateString()}
                        </span>
                        {conflict.assigned_to && (
                          <span>Được giao cho: {conflict.assigned_to}</span>
                        )}
                        {conflict.auto_resolution_suggestions && (
                          <span className="text-blue-600 dark:text-blue-400">
                            {conflict.auto_resolution_suggestions.length} gợi ý
                            AI
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => handleViewDetails(conflict)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-600"
                        title="Xem chi tiết"
                      >
                        <Eye size={16} />
                      </button>
                      {conflict.status === "detected" && (
                        <button
                          onClick={() => handleAutoResolve(conflict.id)}
                          className="p-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30"
                          title="Tự động giải quyết"
                        >
                          <Zap size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Details Modal */}
        <ConflictDetailsModal
          conflict={selectedConflict}
          isOpen={showDetails}
          onClose={() => setShowDetails(false)}
          onResolve={handleResolveConflict}
          onAutoResolve={handleAutoResolve}
          onApplySuggestion={handleApplySuggestion}
        />
      </div>
    </div>
  );
};

export default ConflictsPage;
