import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DataTable,
  Dialog,
  Progress,
  ScrollArea,
  SimpleColumnDef,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  cn,
  toast,
} from "@/components";
import {
  useCancelPipelineRun,
  usePipeline,
  usePipelineRuns,
  usePipelineStepRuns,
  usePipelineSteps,
  useRunPipeline,
  usePipelineRunReport,
} from "@vbkg/api-client";
import {
  PipelineRun,
  PipelineRunStatus,
  PipelineStep,
  PipelineStepRun,
  PipelineStepType,
  PipelineType,
} from "@vbkg/types";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Braces,
  Brain,
  CheckCircle2,
  ChevronRight,
  Clock,
  Code,
  Database,
  Eye,
  File,
  FileText,
  Filter,
  GitBranch,
  Globe,
  Layers,
  Loader2,
  Network,
  Play,
  RefreshCw,
  RotateCcw,
  Settings,
  Shield,
  Timer,
  TrendingUp,
  Workflow,
  XCircle,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { useParams } from "react-router";

const RunStatusBadge = ({ status }: { status?: PipelineRunStatus }) => {
  switch (status) {
    case PipelineRunStatus.COMPLETED:
      return (
        <Badge
          variant="outline"
          className="bg-green-50 text-green-700 border-green-200"
        >
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Hoàn thành
        </Badge>
      );
    case PipelineRunStatus.RUNNING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-50 animate-pulse text-blue-700 border-blue-200"
        >
          <Clock className="w-3 h-3 mr-1" />
          Đang chạy
        </Badge>
      );
    case PipelineRunStatus.PENDING:
      return (
        <Badge
          variant="outline"
          className="bg-amber-50 animate-pulse text-amber-700 border-amber-200"
        >
          <Clock className="w-3 h-3 mr-1" />
          Đang chờ
        </Badge>
      );
    case PipelineRunStatus.FAILED:
      return (
        <Badge
          variant="outline"
          className="bg-red-50 text-red-700 border-red-200"
        >
          <XCircle className="w-3 h-3 mr-1" />
          Thất bại
        </Badge>
      );
    case PipelineRunStatus.CANCELLED:
      return (
        <Badge
          variant="outline"
          className="bg-gray-50 text-gray-700 border-gray-200"
        >
          <XCircle className="w-3 h-3 mr-1" />
          Hủy
        </Badge>
      );
    default:
      return <Badge variant="outline">Không xác định</Badge>;
  }
};

// Get step type icon with updated mapping
const getStepTypeIcon = (stepType: PipelineStepType) => {
  switch (stepType) {
    case PipelineStepType.FILE_INGESTION:
      return <File className="w-4 h-4 mr-1" />;
    case PipelineStepType.API_INGESTION:
      return <Globe className="w-4 h-4 mr-1" />;
    case PipelineStepType.DATABASE_INGESTION:
      return <Database className="w-4 h-4 mr-1" />;
    case PipelineStepType.TEXT_CHUNKING:
      return <FileText className="w-4 h-4 mr-1" />;
    case PipelineStepType.DATA_CLEANER:
      return <Filter className="w-4 h-4 mr-1" />;
    case PipelineStepType.DATA_VALIDATOR:
      return <Shield className="w-4 h-4 mr-1" />;
    case PipelineStepType.KNOWLEDGE_EXTRACTOR:
      return <Brain className="w-4 h-4 mr-1" />;
    case PipelineStepType.KNOWLEDGE_MAPPING:
      return <Braces className="w-4 h-4 mr-1" />;
    case PipelineStepType.ONTOLOGY_ENRICHMENT:
      return <Layers className="w-4 h-4 mr-1" />;
    case PipelineStepType.ENTITY_RESOLUTION:
      return <Network className="w-4 h-4 mr-1" />;
    case PipelineStepType.ENTITY_FUSION:
      return <GitBranch className="w-4 h-4 mr-1" />;
    case PipelineStepType.ENTITY_ENRICHMENT:
      return <Zap className="w-4 h-4 mr-1" />;
    case PipelineStepType.KG_WRITER:
      return <Database className="w-4 h-4 mr-1" />;
    case PipelineStepType.KG_COMPLETION:
      return <BarChart3 className="w-4 h-4 mr-1" />;
    case PipelineStepType.QUALITY_MONITORING:
      return <Eye className="w-4 h-4 mr-1" />;
    case PipelineStepType.CUSTOM_PYTHON:
      return <Code className="w-4 h-4 mr-1" />;
    default:
      return <Workflow className="w-4 h-4 mr-1" />;
  }
};

// Pipeline type badge component
const TypeBadge = ({
  type,
  className,
}: {
  type: PipelineType;
  className?: string;
}) => {
  switch (type) {
    case PipelineType.EXTRACTION:
      return (
        <Badge
          variant="outline"
          className={cn("bg-blue-50 text-blue-700 border-blue-200", className)}
        >
          Extraction
        </Badge>
      );
    case PipelineType.TRANSFORMATION:
      return (
        <Badge
          variant="outline"
          className={cn(
            "bg-purple-50 text-purple-700 border-purple-200",
            className,
          )}
        >
          Transformation
        </Badge>
      );
    case PipelineType.LOADING:
      return (
        <Badge
          variant="outline"
          className={cn(
            "bg-amber-50 text-amber-700 border-amber-200",
            className,
          )}
        >
          Loading
        </Badge>
      );
    case PipelineType.COMPLETE:
      return (
        <Badge
          variant="outline"
          className={cn(
            "bg-emerald-50 text-emerald-700 border-emerald-200",
            className,
          )}
        >
          Complete
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className={className}>
          Unknown
        </Badge>
      );
  }
};

// Format duration from seconds to human readable
const formatDuration = (seconds: number) => {
  if (!seconds && seconds !== 0) return "N/A";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds}s`;
};

// JSON viewer component for config objects
const JsonViewer = ({ data }: { data: any }) => {
  return (
    <pre className="bg-slate-950 text-wrap text-slate-50 max-h-72 p-4 rounded-md overflow-x-auto text-xs">
      <code>{JSON.stringify(data, null, 2)}</code>
    </pre>
  );
};

// Pipeline step card component with enhanced information
const PipelineStepCard = ({
  step,
  index,
}: {
  step: PipelineStep;
  index: number;
}) => {
  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <Badge className="mr-2 bg-slate-200 text-slate-800 hover:bg-slate-200">
              {index + 1}
            </Badge>
            <CardTitle className="text-lg flex items-center">
              {getStepTypeIcon(step.step_type as PipelineStepType)}
              {step.name}
            </CardTitle>
          </div>
          <div className="flex gap-2">
            <Badge
              variant={step.enabled ? "default" : "outline"}
              className={
                step.enabled
                  ? "bg-green-100 text-green-800 hover:bg-green-100"
                  : "bg-gray-100 text-gray-800 hover:bg-gray-100"
              }
            >
              {step.enabled ? "Enabled" : "Disabled"}
            </Badge>
            {step.parallel_execution && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                Parallel
              </Badge>
            )}
            {step.is_incremental_capable && (
              <Badge variant="outline" className="bg-purple-50 text-purple-700">
                Incremental
              </Badge>
            )}
          </div>
        </div>
        <CardDescription className="flex items-center text-sm">
          {step.step_type}
          {step.description && (
            <span className="ml-2 text-xs text-muted-foreground">
              • {step.description}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Dependencies */}
          {step.depends_on && step.depends_on.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Dependencies
              </h4>
              <div className="flex flex-wrap gap-1">
                {step.depends_on.map((dep) => (
                  <Badge key={dep} variant="outline" className="text-xs">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Error Handling */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-1">
              Error Handling
            </h4>
            <div className="flex gap-2 text-xs">
              <Badge variant="outline">
                On Failure: {step.on_failure || "stop"}
              </Badge>
              <Badge variant="outline">
                Max Retries: {step.max_retries || 3}
              </Badge>
            </div>
          </div>

          {/* Timeout */}
          {step.timeout && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Timeout
              </h4>
              <Badge variant="outline" className="text-xs">
                <Timer className="w-3 h-3 mr-1" />
                {formatDuration(step.timeout)}
              </Badge>
            </div>
          )}

          {/* Inputs */}
          {step.inputs && step.inputs.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Inputs
              </h4>
              <div className="flex flex-wrap gap-1">
                {step.inputs.map((input) => (
                  <Badge key={input} variant="outline" className="text-xs">
                    {input}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="config">
            <AccordionTrigger className="text-sm py-2">
              <div className="flex items-center">
                <Settings className="w-4 h-4 mr-1" />
                Configuration
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <JsonViewer data={step.config} />
            </AccordionContent>
          </AccordionItem>
          {step.incremental_config && (
            <AccordionItem value="incremental">
              <AccordionTrigger className="text-sm py-2">
                <div className="flex items-center">
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Incremental Configuration
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <JsonViewer data={step.incremental_config} />
              </AccordionContent>
            </AccordionItem>
          )}
          {step.resource_requirements && (
            <AccordionItem value="resources">
              <AccordionTrigger className="text-sm py-2">
                Resources
              </AccordionTrigger>
              <AccordionContent>
                <JsonViewer data={step.resource_requirements} />
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>
      </CardContent>
    </Card>
  );
};

// Step run card for showing individual step execution details
const StepRunCard = ({
  stepRun,
  step,
}: {
  stepRun: PipelineStepRun;
  step?: PipelineStep;
}) => {
  const duration =
    stepRun.start_time && stepRun.end_time
      ? Number(
          Number(
            (new Date(stepRun.end_time).getTime() -
              new Date(stepRun.start_time).getTime()) /
              1000,
          ).toFixed(2),
        )
      : undefined;

  return (
    <Card className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <Badge className="mr-2 bg-slate-200 text-slate-800 hover:bg-slate-200">
              {stepRun.run_order}
            </Badge>
            <CardTitle className="text-base flex items-center">
              {step && getStepTypeIcon(step.step_type as PipelineStepType)}
              {step?.name || stepRun.step_id}
            </CardTitle>
          </div>
          <div className="flex gap-2 items-center">
            <RunStatusBadge status={stepRun.status} />
            {Number(stepRun?.retry_count) > 0 && (
              <Badge variant="outline" className="text-xs">
                Retry: {stepRun.retry_count}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
          <div>
            <h4 className="font-medium text-muted-foreground">Start Time</h4>
            <p>
              {stepRun.start_time
                ? new Date(stepRun.start_time).toLocaleString()
                : "N/A"}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-muted-foreground">End Time</h4>
            <p>
              {stepRun.end_time
                ? new Date(stepRun.end_time).toLocaleString()
                : "N/A"}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-muted-foreground">Duration</h4>
            <p>{duration ? formatDuration(duration) : "N/A"}</p>
          </div>
          <div>
            <h4 className="font-medium text-muted-foreground">Task ID</h4>
            <p className="font-mono text-xs">
              {stepRun.celery_task_id || "N/A"}
            </p>
          </div>
        </div>

        {stepRun.error_message && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md mb-3">
            <h4 className="text-sm font-medium flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" /> Error
            </h4>
            <p className="text-sm mt-1">{stepRun.error_message}</p>
          </div>
        )}

        {(stepRun.input_data || stepRun.output_data) && (
          <Accordion type="single" collapsible className="w-full">
            {stepRun.input_data && (
              <AccordionItem value="input">
                <AccordionTrigger className="text-sm py-2">
                  Input Data
                </AccordionTrigger>
                <AccordionContent>
                  <JsonViewer data={stepRun.input_data} />
                </AccordionContent>
              </AccordionItem>
            )}
            {stepRun.output_data && (
              <AccordionItem value="output">
                <AccordionTrigger className="text-sm py-2">
                  Output Data
                </AccordionTrigger>
                <AccordionContent>
                  <JsonViewer data={stepRun.output_data} />
                </AccordionContent>
              </AccordionItem>
            )}
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
};

const getStepRunStats = (
  stepRuns: PipelineStepRun[],
): {
  total: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
  cancelled: number;
  successRate: number;
} => {
  const stats = stepRuns.reduce(
    (acc, run) => {
      acc.total++;
      switch (run.status) {
        case "completed":
          acc.completed++;
          break;
        case "failed":
          acc.failed++;
          break;
        case "running":
          acc.running++;
          break;
        case "pending":
          acc.pending++;
          break;
        case "cancelled":
          acc.cancelled++;
          break;
      }
      return acc;
    },
    {
      total: 0,
      completed: 0,
      failed: 0,
      running: 0,
      pending: 0,
      cancelled: 0,
      successRate: 0,
    },
  );
  stats.successRate =
    stats.total > 0 ? (stats.completed / stats.total) * 100 : 0;
  return stats;
};

// Run detail dialog component with step runs
const RunDetailDialog = ({
  isOpen,
  onClose,
  run,
  steps,
}: {
  isOpen: boolean;
  onClose: () => void;
  run: PipelineRun | null;
  steps?: PipelineStep[];
}) => {
  const { data: { data: stepRuns } = {}, isFetching: loadingStepRuns } =
    usePipelineStepRuns(
      { pipeline_run_id: run?.id || "", limit: 100 },
      {
        enabled: !!run?.id && isOpen,
      },
    );

  const stepRunStats = getStepRunStats(stepRuns || []);

  if (!run) return null;

  return (
    <Dialog title="Run Details" open={isOpen} size="3xl" onOpenChange={onClose}>
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium">Status</h3>
            <RunStatusBadge status={run.status} />
          </div>
          <div>
            <h3 className="text-sm font-medium">Duration</h3>
            <p>{formatDuration(run?.duration || 0)}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium">Start Time</h3>
            <p>
              {run?.start_time
                ? new Date(run.start_time).toLocaleString()
                : "N/A"}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium">End Time</h3>
            <p>
              {run.end_time ? new Date(run.end_time)?.toLocaleString() : "N/A"}
            </p>
          </div>
        </div>

        {/* Step Run Statistics */}
        {stepRuns && stepRuns.length > 0 && (
          <div className="grid grid-cols-6 gap-2">
            <div className="text-center">
              <div className="text-2xl font-bold">{stepRunStats.total}</div>
              <div className="text-xs text-muted-foreground">Total Steps</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {stepRunStats.completed}
              </div>
              <div className="text-xs text-muted-foreground">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {stepRunStats.failed}
              </div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stepRunStats.running}
              </div>
              <div className="text-xs text-muted-foreground">Running</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-600">
                {stepRunStats.pending}
              </div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {stepRunStats.successRate.toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">Success Rate</div>
            </div>
          </div>
        )}

        {run.error_message && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md">
            <h3 className="text-sm font-medium flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" /> Error
            </h3>
            <p className="text-sm mt-1">{run.error_message}</p>
          </div>
        )}

        {/* Step Runs */}
        <div>
          <h3 className="font-medium mb-4">Step Execution Details</h3>
          {loadingStepRuns ? (
            <div className="flex justify-center py-6">
              <div className="animate-spin h-6 w-6 border-4 border-primary border-t-transparent rounded-full"></div>
            </div>
          ) : stepRuns && stepRuns.length > 0 ? (
            <div className="space-y-3">
              {stepRuns
                .sort((a, b) => a.run_order - b.run_order)
                .map((stepRun) => {
                  const step = steps?.find((s) => s.id === stepRun.step_id);
                  return (
                    <StepRunCard
                      key={stepRun.id}
                      stepRun={stepRun}
                      step={step}
                    />
                  );
                })}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              No step execution details available.
            </div>
          )}
        </div>

        {run.stats && (
          <div>
            <h3 className="text-sm font-medium mb-2">Statistics</h3>
            <JsonViewer data={run.stats} />
          </div>
        )}

        {run.log && (
          <div>
            <h3 className="text-sm font-medium mb-2">Logs</h3>
            <pre className="bg-black text-wrap text-green-400 p-4 rounded-md overflow-x-auto text-xs h-[200px] overflow-y-auto">
              {run.log}
            </pre>
          </div>
        )}
      </div>

      <div className="flex justify-end mt-4">
        <Button onClick={onClose} variant="outline">
          Đóng
        </Button>
      </div>
    </Dialog>
  );
};

const ReportDialog = ({
  isOpen,
  run,
  onClose,
}: {
  isOpen: boolean;
  run: any;
  onClose: () => void;
}) => {
  const { data: report } = usePipelineRunReport({
    pipeline_run_id: run?.id || "",
  });

  const getLevelColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "excellent":
        return "text-green-600 bg-green-50";
      case "good":
        return "text-blue-600 bg-blue-50";
      case "poor":
        return "text-orange-600 bg-orange-50";
      case "critical":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case "high":
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-blue-500" />;
    }
  };

  if (!report?.data) return null;

  const { data } = report;

  return (
    <Dialog title="Báo cáo" size="2xl" open={isOpen} onOpenChange={onClose}>
      <ScrollArea className="px-6 pb-6">
        <div className="space-y-4">
          {/* Overall Score */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Điểm tổng quan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Điểm số:</span>
                <div className="flex items-center gap-2">
                  <Progress value={data.overall_score * 100} className="w-24" />
                  <span className="font-medium">
                    {(data.overall_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Mức độ:</span>
                <Badge className={getLevelColor(data.overall_level)}>
                  {data.overall_level}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  Entities:{" "}
                  <span className="font-medium">{data.entity_count}</span>
                </div>
                <div>
                  Relationships:{" "}
                  <span className="font-medium">{data.relationship_count}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Dimension Scores */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Điểm theo chiều</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(data.dimension_scores).map(
                  ([key, value]: any) => (
                    <div
                      key={key}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm capitalize font-medium">
                        {key}:
                      </span>
                      <div className="flex items-center gap-2">
                        <Progress value={value?.score * 100} className="w-16" />
                        <span className="text-sm w-12">
                          {(value?.score * 100).toFixed(0)}%
                        </span>
                        <Badge className={getLevelColor(value?.level)}>
                          {value?.level}
                        </Badge>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          {data.recommendations?.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Khuyến nghị</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className="border-l-4 border-orange-200 pl-4 py-2"
                    >
                      <div className="flex items-start gap-2">
                        {getPriorityIcon(rec.priority)}
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium">{rec.message}</p>
                          <p className="text-xs text-gray-600">
                            {rec.suggestion}
                          </p>
                          <Badge variant="outline">
                            {rec.priority} priority
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Vietnamese Analysis */}
          {data.vietnamese_analysis && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Phân tích tiếng Việt</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Banking Coverage:</span>
                    <span className="ml-2 font-medium">
                      {data.vietnamese_analysis.banking_domain_coverage?.banking_percentage?.toFixed(
                        1,
                      ) || 0}
                      %
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Vietnamese Entities:</span>
                    <span className="ml-2 font-medium">
                      {data.vietnamese_analysis.vietnamese_entity_stats?.vietnamese_percentage?.toFixed(
                        1,
                      ) || 0}
                      %
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>
    </Dialog>
  );
};

export default function PipelineDetailsPage() {
  const navigate = useNavigate();
  const { id } = useParams() as { id: string };

  const [selectedRun, setSelectedRun] = useState<PipelineRun | null>(null);
  const [showRunDialog, setShowRunDialog] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);

  const { data: { data: pipeline } = {}, isFetching: loading } = usePipeline({
    id: id,
  });

  const { data: { data: runs = [] } = {}, refetch: refetchRuns } =
    usePipelineRuns({
      pipeline_id: id,
      limit: 100,
    });

  const { data: { data: steps } = {} } = usePipelineSteps({
    pipeline_id: id,
  });

  const { mutate: runPipeline, isPending: isRunning } = useRunPipeline({
    onSuccess: () => {
      toast.success("Bắt đầu pipeline thành công!");
    },

    onError: (error) => {
      console.error("Failed to run pipeline:", error);
      toast.error("Lỗi khi bắt đầu pipeline. Vui lòng thử lại sau.");
    },
  });

  const { mutate: cancelPipelineRun } = useCancelPipelineRun({
    onSuccess: () => {
      toast.success("Hủy pipeline thành công!");
    },
    onError: (error) => {
      console.error("Failed to cancel pipeline:", error);
      toast.error("Lỗi khi hủy pipeline. Vui lòng thử lại sau.");
    },
  });

  const handleBackToList = () => {
    navigate("/admin/data/pipelines");
  };

  const handleRunPipeline = async () => {
    if (!pipeline || !id) return;
    runPipeline({
      id,
    });
  };

  const handleViewRun = (run: PipelineRun) => {
    setSelectedRun(run);
    setShowRunDialog(true);
  };

  const runColumns: SimpleColumnDef<PipelineRun, any>[] = [
    {
      header: "Run ID",
      accessorKey: "id",
      cell: (row) => <div className="font-mono text-xs">{row?.id}</div>,
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (row) => <RunStatusBadge status={row?.status} />,
    },
    {
      header: "Start Time",
      accessorKey: "start_time",
      cell: (row) => (
        <div className="text-sm">
          {row?.start_time ? new Date(row.start_time).toLocaleString() : "N/A"}
        </div>
      ),
    },
    {
      header: "Duration",
      accessorKey: "duration",
      cell: (row) => <div>{formatDuration(row?.duration || 0)}</div>,
    },
    {
      header: "Triggered By",
      accessorKey: "triggered_by",
      cell: (row) => (
        <div className="text-sm">{row?.triggered_by || "System"}</div>
      ),
    },
    {
      header: "Error",
      accessorKey: "error_message",
      cell: (row) =>
        row?.error_message ? (
          <div
            className="text-red-600 truncate max-w-xs"
            title={row.error_message}
          >
            <AlertCircle className="inline w-3 h-3 mr-1" />
            {row.error_message}
          </div>
        ) : null,
    },
  ];

  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center">
          <Button size="sm" onClick={handleBackToList} variant={"outline"}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Pipelines
          </Button>
        </div>
        <Card>
          <CardContent className="py-10">
            <div className="flex justify-center">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center">
          <Button size="sm" onClick={handleBackToList} variant={"outline"}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Pipelines
          </Button>
        </div>
        <Card>
          <CardContent className="py-10">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <h2 className="text-lg font-semibold">Pipeline Not Found</h2>
              <p className="text-muted-foreground mt-2">
                The requested pipeline could not be found.
              </p>
              <Button className="mt-4" onClick={handleBackToList}>
                Return to Pipeline List
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center mb-4">
        <Button size="sm" onClick={handleBackToList} variant={"outline"}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Quay lại danh sách
        </Button>
      </div>

      <div className="flex justify-between items-start gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gap-4 flex-col flex">
            {pipeline.name}
          </h1>
          <p className="text-muted-foreground mt-1 text-lg">
            {pipeline.description}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => refetchRuns()} variant="outline">
            <RotateCcw className="mr-2 h-4 w-4" />
            Cập nhật
          </Button>
          <Button
            onClick={handleRunPipeline}
            disabled={!pipeline.is_active || isRunning}
          >
            {isRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}{" "}
            Chạy
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Tổng quan</TabsTrigger>
          <TabsTrigger value="steps">Các bước</TabsTrigger>
          <TabsTrigger value="runs">Lịch sử</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle> Thông tin Pipeline</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Pipeline ID
                    </dt>
                    <dd className="text-sm font-mono">{pipeline.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Loại
                    </dt>
                    <dd>
                      <TypeBadge type={pipeline.pipeline_type} />
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Lịch
                    </dt>
                    <dd className="text-sm font-mono">
                      {pipeline.schedule || "Not scheduled"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Tổng số bước
                    </dt>
                    <dd className="text-sm">
                      {steps?.length || pipeline.steps?.length || 0}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Tạo bởi
                    </dt>
                    <dd className="text-sm">
                      {pipeline.created_by || "System"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Thời gian tạo
                    </dt>
                    <dd className="text-sm">
                      {pipeline.created_at
                        ? new Date(pipeline.created_at).toLocaleDateString()
                        : ""}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Cập nhật lúc
                    </dt>
                    <dd className="text-sm">
                      {pipeline.updated_at
                        ? new Date(pipeline.updated_at).toLocaleDateString()
                        : ""}
                    </dd>
                  </div>
                </dl>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Gần Đây</CardTitle>
                <CardDescription>
                  {runs?.slice(0, 5).length || 0} lần thực thi gần nhất
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!runs || runs.length === 0 ? (
                  <div className="text-center py-6">
                    <p className="text-muted-foreground">
                      No runs recorded for this pipeline.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {runs.slice(0, 5).map((run) => (
                      <div
                        key={run.id}
                        className="flex flex-wrap justify-between items-center overflow-hidden border-b pb-4 last:border-0"
                      >
                        <div>
                          <div className="flex items-center">
                            <RunStatusBadge status={run.status} />
                          </div>
                          <div className="text-sm mt-1 text-neutral-600 font-light">
                            Thời gian {formatDuration(run.duration || 0)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-muted-foreground mt-1">
                            {run.start_time
                              ? new Date(run.start_time).toLocaleString()
                              : ""}
                          </div>
                          <div className="flex items-center justify-end gap-3">
                            {run.status === "completed" && (
                              <>
                                <Button
                                  size="sm"
                                  className="text-xs mt-1"
                                  variant="outline"
                                  onClick={() => {
                                    navigate(
                                      `/admin/logs?pipeline_run_id=${run.id}`,
                                    );
                                  }}
                                >
                                  Logs
                                </Button>
                                <Button
                                  size="sm"
                                  className="text-xs mt-1"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedRun(run);
                                    setShowReportDialog(true);
                                  }}
                                >
                                  Xem báo cáo
                                </Button>
                              </>
                            )}
                            <Button
                              size="sm"
                              className="text-xs mt-1"
                              variant="default"
                              onClick={() => handleViewRun(run)}
                            >
                              Chi tiết
                            </Button>
                            {run.status === "running" && (
                              <Button
                                size="sm"
                                className="text-xs mt-1"
                                variant="destructive"
                                onClick={() =>
                                  cancelPipelineRun({
                                    id: run.id,
                                    pipeline_id: run.pipeline_id,
                                  })
                                }
                              >
                                Hủy
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>Các bước ({steps?.length || 0})</CardTitle>
              <CardDescription>
                Các bước trong pipeline này, bao gồm tên, loại, trạng thái và
                cấu hình chi tiết.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {steps && steps.length > 0 ? (
                  steps
                    .sort((a, b) => a.run_order - b.run_order)
                    .map((step: PipelineStep, index: number) => (
                      <PipelineStepCard
                        key={step.id}
                        step={step}
                        index={index}
                      />
                    ))
                ) : (
                  <div className="text-center py-6">
                    <p className="text-muted-foreground">
                      Không có bước nào trong pipeline này.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="runs" id="runs-tab">
          <Card>
            <CardHeader>
              <CardTitle>Lịch sử ({runs?.length || 0})</CardTitle>
              <CardDescription>
                Lịch sử các lần chạy pipeline, bao gồm trạng thái, thời gian bắt
                đầu và kết thúc, cùng với thông tin lỗi nếu có.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<PipelineRun, any>
                data={runs || []}
                columns={runColumns}
                showPagination={true}
                actionsOptions={{
                  show: true,
                  position: "end",
                  actions: [
                    {
                      label: "View Details",
                      icon: <ChevronRight className="h-4 w-4" />,
                      onClick: handleViewRun,
                      variant: "ghost",
                    },
                  ],
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <RunDetailDialog
        isOpen={showRunDialog}
        onClose={() => setShowRunDialog(false)}
        run={selectedRun}
        steps={steps}
      />
      <ReportDialog
        isOpen={showReportDialog}
        onClose={() => setShowReportDialog(false)}
        run={selectedRun}
      />
    </div>
  );
}
