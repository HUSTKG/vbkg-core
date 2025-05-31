import { useDeletePipeline, usePipelines } from "@vbkg/api-client";
import { Pipeline, PipelineType } from "@vbkg/types";
import {
  Badge,
  ConfirmDialog,
  DataTable,
  SimpleColumnDef,
  toast,
} from "@vbkg/ui";
import { CheckCircle2, Clock, Edit, Eye, Play, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

// Pipeline type badge component
const TypeBadge = ({ type }: { type?: PipelineType }) => {
  switch (type) {
    case PipelineType.EXTRACTION:
      return (
        <Badge
          variant="outline"
          className="bg-blue-50 text-blue-700 border-blue-200"
        >
          Extraction
        </Badge>
      );
    case PipelineType.TRANSFORMATION:
      return (
        <Badge
          variant="outline"
          className="bg-purple-50 text-purple-700 border-purple-200"
        >
          Transformation
        </Badge>
      );
    case PipelineType.LOADING:
      return (
        <Badge
          variant="outline"
          className="bg-amber-50 text-amber-700 border-amber-200"
        >
          Loading
        </Badge>
      );
    case PipelineType.COMPLETE:
      return (
        <Badge
          variant="outline"
          className="bg-emerald-50 text-emerald-700 border-emerald-200"
        >
          Complete
        </Badge>
      );
    default:
      return <Badge variant="outline">Unknown</Badge>;
  }
};
// Status badge component
const StatusBadge = ({ isActive }: { isActive?: boolean }) => {
  return isActive ? (
    <Badge
      variant="outline"
      className="bg-green-50 text-green-700 border-green-200"
    >
      <CheckCircle2 className="w-3 h-3 mr-1" />
      Active
    </Badge>
  ) : (
    <Badge
      variant="outline"
      className="bg-gray-50 text-gray-700 border-gray-200"
    >
      <Clock className="w-3 h-3 mr-1" />
      Inactive
    </Badge>
  );
};

export default function DataPipelineTable() {
  const { data: pipelines } = usePipelines({});
  const navigate = useNavigate();
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(
    null,
  );
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const columns: SimpleColumnDef<Pipeline, any>[] = [
    {
      header: "Name",
      accessorKey: "name",
      cell: (row) => <div className="font-medium">{row?.name}</div>,
    },
    {
      header: "Description",
      accessorKey: "description",
      cell: (row) => (
        <div className="text-sm text-muted-foreground max-w-md truncate">
          {row?.description || "No description"}
        </div>
      ),
    },
    {
      header: "Type",
      accessorKey: "pipeline_type",
      cell: (row) => <TypeBadge type={row?.pipeline_type} />,
    },
    {
      header: "Steps",
      accessorKey: "steps",
      cell: (row) => (
        <div className="text-center">{row?.steps?.length || 0}</div>
      ),
      enableSorting: false,
    },
    {
      header: "Status",
      accessorKey: "is_active",
      cell: (row) => <StatusBadge isActive={row?.is_active} />,
    },
    {
      header: "Schedule",
      accessorKey: "schedule",
      cell: (row) => (
        <div className="font-mono text-xs">
          {row?.schedule || "No schedule"}
        </div>
      ),
    },
    {
      header: "Last Updated",
      accessorKey: "updated_at",
      cell: (row) => (
        <div className="text-sm">
          {row?.updated_at
            ? new Date(row.updated_at).toLocaleDateString()
            : "N/A"}
        </div>
      ),
    },
  ];
  const { mutate: deletePipeline } = useDeletePipeline({
    onSuccess: () => {
      toast("Success", {
        description: "Pipeline deleted successfully.",
      });
      setShowDeleteDialog(false);
      setSelectedPipeline(null);
    },
    onError: () => {
      toast("Error", {
        description: "Failed to delete pipeline. Please try again.",
        className: "bg-red-500 text-white",
      });
    },
  });
  const { mutate: runPipeline } = useDeletePipeline({
    onSuccess: () => {
      toast("Success", {
        description: "Pipeline run successfully.",
      });
    },
    onError: () => {
      toast("Error", {
        description: "Failed to start pipeline. Please try again.",
        className: "bg-red-500 text-white",
      });
    },
  });

  const confirmDeletePipeline = async () => {
    if (!selectedPipeline) return;
    deletePipeline({ id: selectedPipeline.id });
  };

  const handleRunPipeline = async (pipeline?: Pipeline) => {
    if (!pipeline) return;
    runPipeline({ id: pipeline.id });
  };

  const handleDeletePipeline = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline);
    setShowDeleteDialog(true);
  };

  const handleViewPipeline = (pipeline: Pipeline) => {
    navigate(`./${pipeline.id}`);
  };

  const handleEditPipeline = (pipeline: Pipeline) => {
    navigate(`./${pipeline.id}/edit`);
  };
  return (
    <>
      <DataTable<Pipeline, any>
        data={pipelines?.data}
        columns={columns}
        showGlobalFilter={true}
        showColumnFilters={true}
        showPagination={true}
        actionsOptions={{
          show: true,
          position: "end",
          actions: [
            {
              label: "View Details",
              icon: <Eye className="h-4 w-4" />,
              onClick: handleViewPipeline,
              variant: "ghost",
            },
            {
              label: "Run Pipeline",
              icon: <Play className="h-4 w-4" />,
              onClick: handleRunPipeline,
              variant: "outline",
              className: "text-green-600 hover:text-green-700",
            },
            {
              label: "Edit",
              icon: <Edit className="h-4 w-4" />,
              onClick: handleEditPipeline,
              variant: "outline",
            },
            {
              label: "Delete",
              icon: <Trash2 className="h-4 w-4" />,
              onClick: handleDeletePipeline,
              variant: "outline",
              className: "text-red-600 hover:text-red-700",
            },
          ],
          showInDropdown: true,
          dropdownLabel: "Actions",
        }}
      />
      {selectedPipeline && (
        <ConfirmDialog
          isOpen={showDeleteDialog}
          type="delete"
          onCancel={() => setShowDeleteDialog(false)}
          onConfirm={confirmDeletePipeline}
          message={`Are you sure you want to delete the pipeline "${selectedPipeline.name}"? This action cannot be undone.`}
          title={`Delete Pipeline "${selectedPipeline.name}"`}
        />
      )}
    </>
  );
}
