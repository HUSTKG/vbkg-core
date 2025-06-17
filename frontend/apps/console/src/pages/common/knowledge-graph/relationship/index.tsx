import {
	useKGRelationshipsSearch,
	useRelationshipTypes,
} from "@vbkg/api-client";
import {
	Card,
	CardContent,
	Input,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Switch,
} from "@/components";
import { Circle, Search } from "lucide-react";
import { useState } from "react";
import { useDebounce } from "use-debounce";
import RelationshipTable from "./components/table/RelationshipTable";

export default function KnowledgeGraphRelationships() {
	const [searchQuery, setSearchQuery] = useState("");
	const [selectedType, setSelectedType] = useState("all");
	const [confidenceThreshold, setConfidenceThreshold] = useState<string>();
	const [onlyVerified, setOnlyVerified] = useState(false);

	const { data: relationshipTypes } = useRelationshipTypes({});

	const [query] = useDebounce(searchQuery, 500);

	const { data: relationships } =
		useKGRelationshipsSearch({
			query,
			relationship_types: selectedType !== "all" ? [selectedType] : undefined,
			limit: 10000,
			min_confidence: Number(confidenceThreshold) || 0.5,
			verified_only: onlyVerified,
		}).data || {};

	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div>
					<h1 className="text-3xl font-bold">🔗 Quản lý quan hệ</h1>
					<p className="text-muted-foreground mt-2">
						Quản lý và tìm kiếm các mối quan hệ trong Knowledge Graph của bạn.
						Bạn có thể tìm kiếm theo loại, thực thể, hoặc thuộc tính của mối
						quan hệ.
					</p>
				</div>
				<div className="flex gap-2"></div>
			</div>

			{/* Search and Filters */}
			<Card>
				<CardContent className="p-6">
					<div className="flex flex-col sm:flex-row gap-4">
						<div className="flex-1">
							<div className="relative">
								<Search
									className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
									size={16}
								/>
								<Input
									placeholder="Tìm kiếm mối quan hệ..."
									value={searchQuery}
									onChange={(e) => setSearchQuery(e.target.value)}
									className="pl-10"
								/>
							</div>
						</div>
						<div className="flex items-center gap-2">
							<Switch
								id="only-verified"
								checked={onlyVerified}
								onCheckedChange={(val) => setOnlyVerified(val)}
							/>
							<label htmlFor="only-verified" className="text-sm">
								Chỉ xác minh
							</label>
						</div>
						<Input
							placeholder="Độ tin cậy tối thiểu"
							value={confidenceThreshold}
							className="w-48"
							onChange={(e) => setConfidenceThreshold(e.target.value)}
						/>
						<Select value={selectedType} onValueChange={setSelectedType}>
							<SelectTrigger className="w-[180px]">
								<SelectValue placeholder="Loại quan hệ" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="all">
									Tất cả loại quan hệ
								</SelectItem>
								{relationshipTypes?.data?.map((type) => (
									<SelectItem key={type.id} value={type.name}>
										<Circle size={16} className="mr-2" color={type.color} />
										{type.display_name}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
				</CardContent>
			</Card>

			{/* Relationships Table */}
			<RelationshipTable relationships={relationships || []} />
		</div>
	);
}
