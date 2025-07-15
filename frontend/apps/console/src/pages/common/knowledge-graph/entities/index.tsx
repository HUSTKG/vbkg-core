import {
  Card,
  CardContent,
  Input,
  // Select,
  // SelectContent,
  // SelectItem,
  // SelectTrigger,
  // SelectValue,
  Switch,
} from "@/components";
import { useKGEntitiesSearch } from "@vbkg/api-client";
import { Search } from "lucide-react";
import { useState } from "react";
import EntitiesTable from "./components/dialogs/EntitiesTable";
import { useDebounce } from "use-debounce";
import { useSearchParams } from "react-router";

export default function KnowledgeGraphEntities() {
  const [searchQuery, setSearchQuery] = useState("");
  // const [selectedType, setSelectedType] = useState("all");
  const [confidenceThreshold, setConfidenceThreshold] = useState<string>();
  const [semanticSearchEnabled, setSemanticSearchEnabled] = useState(false);
  const [onlyVerified, setOnlyVerified] = useState(false);
  const [searchParams] = useSearchParams();

  const page = Number(searchParams.get("page")) || 1;
  const limit = Number(searchParams.get("pageSize")) || 10;

  const [query] = useDebounce(searchQuery, 500);

  const { data: entities } =
    useKGEntitiesSearch({
      limit,
      skip: (page - 1) * limit,
      semantic_search: semanticSearchEnabled,
      min_confidence: Number(confidenceThreshold) || 0.5,
      verified_only: onlyVerified,
      query,
    }) || {};

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">🏢 Quản lý thực thể</h1>
          <p className="text-muted-foreground mt-2">
            Quản lý và tìm kiếm các thực thể trong Knowledge Graph của bạn. Bạn
            có thể tìm kiếm theo tên, loại, hoặc thuộc tính của thực thể.
          </p>
        </div>
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
                  placeholder="Tìm kiếm thực thể..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="semantic-search"
                checked={semanticSearchEnabled}
                onCheckedChange={(val) => setSemanticSearchEnabled(val)}
              />
              <label htmlFor="semantic-search" className="text-sm">
                Theo ngữ nghĩa
              </label>
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
            {/* <Select value={selectedType} onValueChange={setSelectedType}> */}
            {/* 	<SelectTrigger className="w-[180px]"> */}
            {/* 		<SelectValue placeholder="Loại thực thể" /> */}
            {/* 	</SelectTrigger> */}
            {/* 	<SelectContent> */}
            {/* 		<SelectItem value="all">Tất cả loại</SelectItem> */}
            {/* 		{entityTypes?.data?.map((type) => ( */}
            {/* 			<SelectItem key={type.id} value={type.name}> */}
            {/* 				<Circle size={16} className="mr-2" color={type.color} /> */}
            {/* 				{type.display_name} */}
            {/* 			</SelectItem> */}
            {/* 		))} */}
            {/* 		<SelectItem value="custom">Loại tuỳ chỉnh</SelectItem> */}
            {/* 	</SelectContent> */}
            {/* </Select> */}
          </div>
        </CardContent>
      </Card>

      <EntitiesTable entities={entities} />
    </div>
  );
}
