import { Badge, Dialog } from "@/components";
import { Relationship } from "@vbkg/types";

interface ViewRelationshipDialogProps {
	showDetailsDialog: boolean;
	setShowDetailsDialog: (open: boolean) => void;
	selectedRelationship?: Relationship;
}

export default function ViewRelationshipDialog({
	showDetailsDialog,
	setShowDetailsDialog,
	selectedRelationship,
}: ViewRelationshipDialogProps) {
	return (
		<Dialog
			title="Relationship Details"
			description="Detailed information about the selected entity"
			open={showDetailsDialog}
			size="2xl"
			onOpenChange={setShowDetailsDialog}
		>
			{selectedRelationship && (
				<div className="space-y-6">
					{/* Basic Info */}
					<div className="grid grid-cols-2 gap-4">
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Relationship Type
							</span>
							<div className="mt-1">
								<Badge variant="outline" className="mt-1 uppercase">
									{selectedRelationship.relationship_type}
								</Badge>
							</div>
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
											width: `${Number(selectedRelationship?.confidence) * 100}%`,
										}}
									/>
								</div>
								<span className="text-sm">
									{Math.round(Number(selectedRelationship.confidence) * 100)}%
								</span>
							</div>
						</div>
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Source Entity
							</span>
							<div className="mt-1">
								<Badge variant="secondary" className="text-xs">
									{selectedRelationship.source_entity.entity_text}
								</Badge>
							</div>
						</div>
						<div>
							<span className="text-sm font-medium text-muted-foreground">
								Target Entity
							</span>
							<div className="mt-1">
								<Badge variant="outline" className="mt-1">
									{selectedRelationship.target_entity.entity_text}
								</Badge>
							</div>
						</div>
					</div>
					<div>
						{/* biome-ignore lint/a11y/noLabelWithoutControl: <explanation> */}
						<label className="text-sm font-medium text-muted-foreground">
							Status
						</label>
						<div className="mt-1">
							{selectedRelationship.is_verified ? (
								<Badge variant="default" className="bg-green-500">
									Verified
								</Badge>
							) : (
								<Badge variant="secondary">Pending</Badge>
							)}
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
								{JSON.stringify(selectedRelationship.properties, null, 2)}
							</pre>
						</div>
					</div>
				</div>
			)}
		</Dialog>
	);
}
