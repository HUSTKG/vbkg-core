import { useState } from "react";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Database,
  RefreshCw,
  Play,
  Eye,
} from "lucide-react";
import { ActivityStatus, RecentActivityItem, StatisticCard } from "@vbkg/ui";
import { useQualityDashboard } from "@vbkg/api-client";

const QualityMetricBar = ({ label, score }: any) => {
  const percentage = Math.round(score * 100);
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500",
  };

  const getColor = (score: any) => {
    if (score >= 0.9) return "green";
    if (score >= 0.7) return "blue";
    if (score >= 0.5) return "yellow";
    return "red";
  };

  const barColor = colorClasses[getColor(score)];

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {percentage}%
        </span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`${barColor} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const QualityDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const { data: dashboard } = useQualityDashboard({}).data || {};

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setRefreshing(false);
  };

  const handleRunMonitoring = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setLoading(false);
    alert("Đã bắt đầu chạy kiểm tra chất lượng tự động");
  };

  const qualityScore = dashboard?.quality_report.overall_score || 0;

  const getScoreColor = (score: any) => {
    if (score >= 0.9) return "text-green-600";
    if (score >= 0.7) return "text-blue-600";
    if (score >= 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Quality Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Tổng quan về chất lượng dữ liệu Knowledge Graph
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
                />
                {refreshing ? "Đang tải..." : "Làm mới"}
              </button>
              <button
                onClick={handleRunMonitoring}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Play className="h-4 w-4 mr-2" />
                {loading ? "Đang chạy..." : "Chạy kiểm tra"}
              </button>
            </div>
          </div>
        </div>

        {/* Overall Quality Score */}
        <div className="mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-center">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Điểm chất lượng tổng thể
              </h2>
              <div
                className={`text-6xl font-bold ${getScoreColor(qualityScore)} mb-2`}
              >
                {Math.round(qualityScore * 100)}
              </div>
              <div className="text-gray-500 dark:text-gray-400">
                {dashboard?.trending_metrics.trend === "improving" && (
                  <span className="text-green-600 dark:text-green-400">
                    ↗️ Đang cải thiện
                  </span>
                )}
                {dashboard?.trending_metrics.trend === "declining" && (
                  <span className="text-red-600 dark:text-red-400">
                    ↘️ Đang giảm
                  </span>
                )}
                {dashboard?.trending_metrics.trend === "stable" && (
                  <span className="text-blue-600 dark:text-blue-400">
                    ➡️ Ổn định
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Key Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatisticCard
            title="Tổng số Entities"
            value={
              dashboard?.quality_report.total_entities.toLocaleString() || "0"
            }
            icon={<Database size={20} />}
            color="blue"
          />
          <StatisticCard
            title="Tổng số Relationships"
            value={
              dashboard?.quality_report.total_relationships.toLocaleString() ||
              "0"
            }
            icon={<BarChart3 size={20} />}
            color="green"
          />
          <StatisticCard
            title="Xung đột chờ xử lý"
            value={dashboard?.quality_report.conflicts_pending || 0}
            icon={<AlertTriangle size={20} />}
            color="yellow"
            description="Cần được giải quyết"
          />
          <StatisticCard
            title="Vấn đề phát hiện"
            value={dashboard?.quality_report.issues_detected || 0}
            icon={<Eye size={20} />}
            color="red"
            description="Tổng số vấn đề"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Quality Dimensions */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Chỉ số chất lượng theo từng khía cạnh
            </h3>
            <div className="space-y-4">
              <QualityMetricBar
                label="Completeness (Tính đầy đủ)"
                score={dashboard?.quality_report.dimension_scores.completeness}
              />
              <QualityMetricBar
                label="Accuracy (Tính chính xác)"
                score={dashboard?.quality_report.dimension_scores.accuracy}
              />
              <QualityMetricBar
                label="Consistency (Tính nhất quán)"
                score={dashboard?.quality_report.dimension_scores.consistency}
              />
              <QualityMetricBar
                label="Validity (Tính hợp lệ)"
                score={dashboard?.quality_report.dimension_scores.validity}
              />
              <QualityMetricBar
                label="Uniqueness (Tính duy nhất)"
                score={dashboard?.quality_report.dimension_scores.uniqueness}
              />
              <QualityMetricBar
                label="Timeliness (Tính kịp thời)"
                score={dashboard?.quality_report.dimension_scores.timeliness}
              />
            </div>
          </div>

          {/* Conflict Statistics */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Thống kê xung đột
            </h3>

            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Theo trạng thái
              </h4>
              <div className="space-y-2">
                {Object.entries(
                  dashboard?.conflict_statistics.by_status || {},
                ).map(([status, count]) => (
                  <div
                    key={status}
                    className="flex justify-between items-center"
                  >
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {status.replace("_", " ")}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Theo loại xung đột
              </h4>
              <div className="space-y-2">
                {Object.entries(
                  dashboard?.conflict_statistics.by_type || {},
                ).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {type.replace("_", " ")}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Activity */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Hoạt động gần đây
              </h3>
              <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                Xem tất cả
              </button>
            </div>

            <div className="space-y-0">
              {dashboard?.recent_activity.map((activity, index) => (
                <RecentActivityItem
                  key={index}
                  title={activity.description}
                  time={activity.timestamp.toLocaleString()}
                  description={`Bởi ${activity.user}`}
                  status={activity.status as ActivityStatus}
                  icon={
                    activity.type === "conflict_resolution" ? (
                      <CheckCircle size={16} />
                    ) : activity.type === "quality_monitoring" ? (
                      <RefreshCw size={16} />
                    ) : (
                      <Eye size={16} />
                    )
                  }
                />
              ))}
            </div>
          </div>

          {/* Improvement Recommendations */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              Đề xuất cải thiện
            </h3>

            <div className="space-y-4">
              {dashboard?.quality_report.improvement_recommendations.map(
                (recommendation, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {recommendation}
                    </p>
                  </div>
                ),
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Eye className="h-4 w-4 mr-2" />
                Xem báo cáo chi tiết
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QualityDashboard;
