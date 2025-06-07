import { Badge, Button, Dialog } from "@/components";
import { Entity } from "@vbkg/types";
import { ExternalLink } from "lucide-react";
import { useNavigate } from "react-router";

interface ViewEntityDialogProps {
	showDetailsDialog: boolean;
	setShowDetailsDialog: (open: boolean) => void;
	selectedEntity: Entity | null;
}

export default function ViewEntityDialog({
	showDetailsDialog,
	setShowDetailsDialog,
	selectedEntity,
}: ViewEntityDialogProps) {
	const navigate = useNavigate();
	return (
		<Dialog
			title="Entity Details"
			description="Detailed information about the selected entity"
			open={showDetailsDialog}
			size="2xl"
			onOpenChange={setShowDetailsDialog}
		>
			{selectedEntity && (
				<div className="space-y-6">
					{/* Basic Info */}
					<div className="grid grid-cols-2 gap-4">
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Entity Text
							</span>
							<p className="font-medium">{selectedEntity.entity_text}</p>
						</div>
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Entity Type
							</span>
							<Badge variant="outline" className="mt-1">
								{selectedEntity.entity_type}
							</Badge>
						</div>
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Confidence
							</span>
							<div className="flex items-center gap-2 mt-1">
								<div className="w-24 bg-muted rounded-full h-2">
									<div
										className="bg-blue-500 h-2 rounded-full"
										style={{
											width: `${Number(selectedEntity?.confidence) * 100}%`,
										}}
									/>
								</div>
								<span className="text-sm">
									{Math.round(Number(selectedEntity.confidence) * 100)}%
								</span>
							</div>
						</div>
						<div>
							{/* biome-ignore lint/a11y/noLabelWithoutControl: <explanation> */}
							<label className="text-sm font-medium text-muted-foreground">
								Status
							</label>
							<div className="mt-1">
								{selectedEntity.is_verified ? (
									<Badge variant="default" className="bg-green-500">
										Verified
									</Badge>
								) : (
									<Badge variant="secondary">Pending</Badge>
								)}
							</div>
						</div>
					</div>

					{/* Properties */}
					<div>
						{/* biome-ignore lint/a11y/noLabelWithoutControl: <explanation> */}
						<label className="text-sm font-medium text-muted-foreground">
							Properties
						</label>
						<div className="mt-2 p-4 bg-muted rounded-lg">
							<pre className="text-sm">
								{JSON.stringify(selectedEntity.properties, null, 2)}
							</pre>
						</div>
					</div>

					{/* Actions */}
					<div className="flex justify-end gap-2">
						<Button
							onClick={() => {
								navigate(`/admin/kg/explorer?entity_id=${selectedEntity.id}`);
								setShowDetailsDialog(false);
							}}
						>
							<ExternalLink size={16} className="mr-2" />
							View in Graph
						</Button>
					</div>
				</div>
			)}
		</Dialog>
	);
}
