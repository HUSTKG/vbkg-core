import { Dialog } from "@/components";
import FormCreateVisualization from "./FormCreateVisualization";
import { Visualization } from "@vbkg/types";

interface CreateVisualizationDialogProps {
	open?: boolean;
	onOpenChange: (open: boolean) => void;
	mode: "create" | "edit";
	editingVisualization?: Visualization | null;
	setEditingVisualization?: (visualization: any) => void;
}

export default function CreateVisualizationDialog({
	mode,
	open,
	onOpenChange,
	setEditingVisualization,
	editingVisualization,
}: CreateVisualizationDialogProps) {
	return (
		<Dialog
			title={
				mode === "create" ? "Tạo Visualization" : "Chỉnh sửa Visualization"
			}
			open={open}
			onOpenChange={onOpenChange}
		>
			<div className="p-4">
				<FormCreateVisualization
					setEditingVisualization={setEditingVisualization}
					onOpenChange={onOpenChange}
					editingVisualization={editingVisualization}
				/>
			</div>
		</Dialog>
	);
}
