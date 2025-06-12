import { Button, CustomSheet } from "@/components";
import { FormCreateDataSource } from "../form/FormCreateDataSource";
import { useState } from "react";

export default function CreateDataSourceSheet() {
	const [isOpen, setIsOpen] = useState(false);
	return (
		<CustomSheet
			trigger={<Button>Add Data Source</Button>}
			title="Add Data Source"
			open={isOpen}
			onOpenChange={setIsOpen}
			description="Create a new data source configuration"
			side="right"
			size="lg"
		>
			<div className="px-4">
				<FormCreateDataSource
					onCloseDialog={() => {
						setIsOpen(false);
					}}
				/>
			</div>
		</CustomSheet>
	);
}
