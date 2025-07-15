import { Button, CustomSheet } from "@/components";
import { FormCreateDataSource } from "../form/FormCreateDataSource";
import { useState } from "react";

export default function CreateDataSourceSheet() {
	const [isOpen, setIsOpen] = useState(false);
	return (
		<CustomSheet
			trigger={<Button>Thêm nguồn dữ liệu</Button>}
			title="Thêm nguồn dữ liệu"
			open={isOpen}
			onOpenChange={setIsOpen}
			description="Tạo cấu hình nguồn dữ liệu mới"
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
