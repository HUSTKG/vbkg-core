import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components";
import DataPipelineTable from "./components/table/list";

export default function PipelineListPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Pipelines</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Management</CardTitle>
          <CardDescription>
            View, create, edit and run your data pipelines.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataPipelineTable />
        </CardContent>
      </Card>
    </div>
  );
}
