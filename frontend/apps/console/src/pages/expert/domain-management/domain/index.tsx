import React, { useState } from "react";
import { Database, Settings, BarChart3 } from "lucide-react";
import * as z from "zod";
import {
	Badge,
	Button,
	Card,
	CardContent,
	CardHeader,
	CardTitle,
	StatisticCard,
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
	toast,
} from "@/components";
import CreateDomainDialog from "./dialog/create";
import {
	useCreateDomain,
	useDomains,
	useDomainStats,
	useDomainOverview,
} from "@vbkg/api-client";
import { CreateDomainSchema } from "@vbkg/schemas";
import DomainListTable from "./table/list-domain";

const DomainManagementPage: React.FC = () => {
	const { data: domainResponse } = useDomains({
		limit: 100,
	});

	const domains = domainResponse?.data || [];

	const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
	const [loading, setLoading] = useState(false);

	const [selectedDomain, setSelectedDomain] = useState<number>();


	const { data: overview } = useDomainOverview({});

	const { mutate: createDomain } = useCreateDomain({
		onSuccess: () => {
			toast("Tạo domain thành công");
		},
		onError: (error) => {
			toast("Tạo domain thất bại: " + error.message);
		},
	});

	const handleCreateDomain = (data: z.infer<typeof CreateDomainSchema>) => {
		setLoading(true);
		createDomain(data);
		setLoading(false);
	};

	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div>
					<h1 className="text-2xl font-bold text-gray-900">Quản Lý Domain</h1>
					<p className="text-gray-600 mt-1">
						Quản lý các domain business cho hệ thống knowledge graph
					</p>
				</div>
				<Button onClick={() => setIsCreateModalOpen(true)}>Tạo Domain</Button>
			</div>

			{/* Statistics */}
			<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
				<StatisticCard
					title="Tổng Domain"
					value={overview?.overview?.total_domains}
					icon={<Database size={20} />}
					color="blue"
				/>
				<StatisticCard
					title="Ontology Classes"
					value={overview?.overview?.total_ontology_classes}
					icon={<Settings size={20} />}
					color="green"
				/>
				<StatisticCard
					title="Ontology Properties"
					value={overview?.overview?.total_ontology_properties}
					icon={<BarChart3 size={20} />}
					color="purple"
				/>
				<StatisticCard
					title="Domain Hoạt Động"
					value={overview?.overview?.active_domains}
					icon={<Database size={20} />}
					color="orange"
				/>
			</div>

			{/* Main Content */}
			<Card>
				<CardHeader>
					<CardTitle>Danh Sách Domain</CardTitle>
				</CardHeader>
				<CardContent>
					<DomainListTable domains={domains} />
				</CardContent>
			</Card>
			<CreateDomainDialog
				isCreateModalOpen={isCreateModalOpen}
				setIsCreateModalOpen={setIsCreateModalOpen}
				handleCreateDomain={handleCreateDomain}
				isLoading={loading}
			/>
		</div>
	);
};

export default DomainManagementPage;
