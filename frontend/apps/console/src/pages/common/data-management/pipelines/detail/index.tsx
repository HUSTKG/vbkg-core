import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileCode,
  Database,
  File,
  Globe,
  Braces,
  Code,
  Brain,
  Network,
  Workflow,
  ChevronRight,
  ArrowLeft,
  Play,
} from "lucide-react";
import {
  PipelineRun,
  PipelineStatus,
  PipelineStep,
  PipelineStepType,
  PipelineType,
} from "@vbkg/types";
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
  CardFooter,
  CardHeader,
  CardTitle,
  cn,
  DataTable,
  Dialog,
  SimpleColumnDef,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@vbkg/ui";
import { useNavigate } from "react-router";
import { useState } from "react";
import { useParams } from "react-router";
import {
  usePipeline,
  usePipelineRuns,
  usePipelineSteps,
  useRunPipeline,
} from "@vbkg/api-client";

const RunStatusBadge = ({ status }: { status?: PipelineStatus }) => {
  switch (status) {
    case PipelineStatus.COMPLETED:
      return (
        <Badge
          variant="outline"
          className="bg-green-50 text-green-700 border-green-200"
        >
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Completed
        </Badge>
      );
    case PipelineStatus.RUNNING:
      return (
        <Badge
          variant="outline"
          className="bg-blue-50 text-blue-700 border-blue-200"
        >
          <Clock className="w-3 h-3 mr-1" />
          Running
        </Badge>
      );
    case PipelineStatus.PENDING:
      return (
        <Badge
          variant="outline"
          className="bg-amber-50 text-amber-700 border-amber-200"
        >
          <Clock className="w-3 h-3 mr-1" />
          Pending
        </Badge>
      );
    case PipelineStatus.FAILED:
      return (
        <Badge
          variant="outline"
          className="bg-red-50 text-red-700 border-red-200"
        >
          <XCircle className="w-3 h-3 mr-1" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">Unknown</Badge>;
  }
};

// Get step type icon
const getStepTypeIcon = (stepType: PipelineStepType) => {
  switch (stepType) {
    case PipelineStepType.FILE_READER:
      return <File className="w-4 h-4 mr-1" />;
    case PipelineStepType.API_FETCHER:
      return <Globe className="w-4 h-4 mr-1" />;
    case PipelineStepType.DATABASE_EXTRACTOR:
      return <Database className="w-4 h-4 mr-1" />;
    case PipelineStepType.TEXT_EXTRACTOR:
      return <FileCode className="w-4 h-4 mr-1" />;
    case PipelineStepType.LLM_ENTITY_EXTRACTOR:
      return <Brain className="w-4 h-4 mr-1" />;
    case PipelineStepType.FIBO_MAPPER:
      return <Braces className="w-4 h-4 mr-1" />;
    case PipelineStepType.ENTITY_RESOLUTION:
      return <Network className="w-4 h-4 mr-1" />;
    case PipelineStepType.KNOWLEDGE_GRAPH_WRITER:
      return <Database className="w-4 h-4 mr-1" />;
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
  if (!seconds) return "N/A";

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
    <pre className="bg-slate-950 text-slate-50 p-4 rounded-md overflow-x-auto text-xs">
      <code>{JSON.stringify(data, null, 2)}</code>
    </pre>
  );
};

// Pipeline step card component
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
        </div>
        <CardDescription className="flex items-center text-sm">
          {step.step_type}
          {step.inputs && step.inputs?.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              Inputs: {step.inputs.join(", ")}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="config">
            <AccordionTrigger className="text-sm py-2">
              Configuration
            </AccordionTrigger>
            <AccordionContent>
              <JsonViewer data={step.config} />
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
};

// Mock logs for a run
const MockLogContent = () => (
  <pre className="text-xs font-mono p-4 bg-black text-green-400 rounded-md h-[300px] overflow-auto">
    {`[2024-05-18T01:00:00] INFO: Starting pipeline run for "Customer Data ETL"
[2024-05-18T01:00:01] INFO: Executing step "Extract CRM Data"
[2024-05-18T01:00:02] INFO: Making API request to https://api.crm.example.com/customers
[2024-05-18T01:01:15] INFO: Received 1,532 customer records
[2024-05-18T01:01:16] INFO: Step "Extract CRM Data" completed successfully
[2024-05-18T01:01:16] INFO: Executing step "Transform Customer Data"
[2024-05-18T01:01:17] INFO: Running Python transformation
[2024-05-18T01:01:18] INFO: Removed sensitive fields from customer records
[2024-05-18T01:02:45] INFO: Step "Transform Customer Data" completed successfully
[2024-05-18T01:02:46] INFO: Executing step "Load to Data Warehouse"
[2024-05-18T01:02:47] INFO: Inserting data into knowledge graph
[2024-05-18T01:02:48] INFO: Processing batch 1/16
[2024-05-18T01:03:15] INFO: Processing batch 2/16
[2024-05-18T01:03:42] INFO: Processing batch 3/16
[2024-05-18T01:04:10] INFO: Processing batch 4/16
[2024-05-18T01:04:45] INFO: Processing batch 5/16
[2024-05-18T01:05:12] INFO: Processing batch 16/16
[2024-05-18T01:05:22] INFO: Step "Load to Data Warehouse" completed successfully
[2024-05-18T01:05:23] INFO: Pipeline run completed successfully`}
  </pre>
);

// Run detail dialog component
const RunDetailDialog = ({
  isOpen,
  onClose,
  run,
}: {
  isOpen: boolean;
  onClose: () => void;
  run: PipelineRun | null;
}) => {
  if (!run) return null;

  return (
    <Dialog title="Run Details" open={isOpen} size="3xl" onOpenChange={onClose}>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium">Status</h3>
            <RunStatusBadge status={run.status} />
          </div>
          <div>
            <h3 className="text-sm font-medium">Duration</h3>
            <p>{formatDuration(run.duration || 0)}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium">Start Time</h3>
            <p>
              {run?.start_time ? new Date(run.start_time).toLocaleString() : ""}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium">End Time</h3>
            <p>
              {run.end_time ? new Date(run.end_time)?.toLocaleString() : "N/A"}
            </p>
          </div>
        </div>

        {run.error_message && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md">
            <h3 className="text-sm font-medium flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" /> Error
            </h3>
            <p className="text-sm mt-1">{run.error_message}</p>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium mb-2">Logs</h3>
          <MockLogContent />
        </div>
      </div>

      <div>
        <Button onClick={onClose}>Close</Button>
      </div>
    </Dialog>
  );
};

export default function PipelineDetailsPage() {
  const navigate = useNavigate();
  const { id } = useParams() as { id: string };

  const [selectedRun, setSelectedRun] = useState<PipelineRun | null>(null);
  const [showRunDialog, setShowRunDialog] = useState(false);

  const { data: { data: pipeline } = {}, isFetching: loading } = usePipeline({
    id: id,
  });

  const { data: { data: runs } = {} } = usePipelineRuns({
    pipeline_id: id,
    limit: 100,
  });

  const { data: { data: steps } = {} } = usePipelineSteps({
    pipeline_id: id,
  });

  const { mutate: runPipeline } = useRunPipeline({
    onSuccess: () => {
      toast("Success", {
        description: `Pipeline "${pipeline?.name}" started successfully.`,
      });
    },

    onError: (error) => {
      console.error("Failed to run pipeline:", error);
      toast("Error", {
        description: "Failed to start pipeline. Please try again.",
        className: "bg-red-500 text-white",
      });
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
          <Button size="sm" onClick={handleBackToList}>
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
          <Button size="sm" onClick={handleBackToList}>
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
        <Button size="sm" onClick={handleBackToList}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Pipelines
        </Button>
      </div>

      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            {pipeline.name}
            <TypeBadge type={pipeline.pipeline_type} className="ml-3" />
            <Badge
              variant={pipeline.is_active ? "default" : "outline"}
              className={`ml-3 ${pipeline.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}
            >
              {pipeline.is_active ? "Active" : "Inactive"}
            </Badge>
          </h1>
          <p className="text-muted-foreground mt-1 text-lg">
            {pipeline.description}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRunPipeline}>
            <Play className="mr-2 h-4 w-4" /> Run Now
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="steps">Pipeline Steps</TabsTrigger>
          <TabsTrigger value="runs">Run History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Information</CardTitle>
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
                      Type
                    </dt>
                    <dd>
                      <TypeBadge type={pipeline.pipeline_type} />
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Schedule
                    </dt>
                    <dd className="text-sm font-mono">
                      {pipeline.schedule || "Not scheduled"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Created
                    </dt>
                    <dd className="text-sm">
                      {pipeline.created_at
                        ? new Date(pipeline.created_at).toLocaleDateString()
                        : ""}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Last Updated
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
                <CardTitle>Recent Runs</CardTitle>
              </CardHeader>
              <CardContent>
                {runs?.length === 0 ? (
                  <div className="text-center py-6">
                    <p className="text-muted-foreground">
                      No runs recorded for this pipeline.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {runs?.slice(0, 3).map((run) => (
                      <div
                        key={run.id}
                        className="flex justify-between items-center border-b pb-4 last:border-0"
                      >
                        <div>
                          <div className="flex items-center">
                            <RunStatusBadge status={run.status} />
                            <span className="ml-2 text-sm font-mono">
                              {run.id}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {run.start_time
                              ? new Date(run.start_time).toLocaleString()
                              : ""}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm">
                            {formatDuration(run.duration || 0)}
                          </div>
                          <Button
                            size="sm"
                            className="text-xs mt-1"
                            onClick={() => handleViewRun(run)}
                          >
                            View Details
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Button
                  size="sm"
                  className="w-full"
                  onClick={() => document.getElementById("runs-tab")?.click()}
                >
                  View All Runs
                </Button>
              </CardFooter>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>Steps ({pipeline.steps?.length})</CardTitle>
              <CardDescription>
                The sequence of operations in this pipeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {steps?.map((step: PipelineStep, index: number) => (
                  <PipelineStepCard key={step.id} step={step} index={index} />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="runs" id="runs-tab">
          <Card>
            <CardHeader>
              <CardTitle>Run History</CardTitle>
              <CardDescription>
                Previous executions of this pipeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<PipelineRun, any>
                data={runs}
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
      />
    </div>
  );
}
