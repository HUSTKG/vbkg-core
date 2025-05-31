import { useKGRelationshipsSearch } from "@vbkg/api-client";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DataTable,
  Dialog,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  StatisticCard,
  Switch,
  Textarea,
} from "@vbkg/ui";
import {
  ArrowRight,
  CheckCircle,
  Clock,
  Download,
  Edit3,
  Eye,
  Filter,
  Network,
  Plus,
  Search,
  Settings,
  Target,
  Trash2,
  Upload,
} from "lucide-react";
import { useState } from "react";

export default function KnowledgeGraphRelationships() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const { relationships: relationships } =
    useKGRelationshipsSearch({
      limit: 200,
    }).data || {};

  const relationshipColumns = [
    {
      header: "Relationship",
      cell: (rel: any) => (
        <Badge variant="outline" className="font-medium uppercase">
          {rel.relationship_type}
        </Badge>
      ),
    },
    {
      header: "Source → Target",
      cell: (rel: any) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="font-medium">{rel.source_entity.entity_text}</div>
            <ArrowRight size={14} className="text-muted-foreground" />
            <div className="font-medium">{rel.target_entity.entity_text}</div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary" className="text-xs">
              {rel.source_entity.entity_type}
            </Badge>
            <ArrowRight size={10} />
            <Badge variant="secondary" className="text-xs">
              {rel.target_entity.entity_type}
            </Badge>
          </div>
        </div>
      ),
    },
    {
      header: "Properties",
      cell: (rel: any) => (
        <div className="space-y-1 max-w-xs line-clamp-2">
          {Object.entries(rel.properties || {})
            .slice(0, 2)
            .map(([key, value]) => (
              <div key={key} className="text-sm">
                <span className="text-muted-foreground">{key}:</span>{" "}
                {String(value)}
              </div>
            ))}
          {Object.keys(rel.properties || {}).length > 2 && (
            <span className="text-xs text-muted-foreground">
              +{Object.keys(rel.properties || {}).length - 2} more
            </span>
          )}
        </div>
      ),
    },
    {
      header: "Confidence",
      cell: (rel: any) => (
        <div className="flex items-center gap-2">
          <div className="w-16 bg-muted rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full"
              style={{ width: `${rel.confidence * 100}%` }}
            />
          </div>
          <span className="text-sm">{Math.round(rel.confidence * 100)}%</span>
        </div>
      ),
    },
    {
      header: "Status",
      cell: (rel: any) =>
        rel.is_verified ? (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle size={12} className="mr-1" />
            Verified
          </Badge>
        ) : (
          <Badge variant="secondary">
            <Clock size={12} className="mr-1" />
            Pending
          </Badge>
        ),
    },
    {
      header: "Created",
      cell: (rel: any) => (
        <span className="text-sm text-muted-foreground">
          {new Date(rel.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      header: "Actions",
      cell: () => (
        <div className="flex gap-1">
          <Button size="sm">
            <Eye size={16} />
          </Button>
          <Button size="sm">
            <Edit3 size={16} />
          </Button>
          <Button size="sm">
            <Trash2 size={16} />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">🔗 Relationships Management</h1>
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
                  placeholder="Search relationships by type, entities, or properties..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Relationship Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="WORKS_FOR">Works For</SelectItem>
                <SelectItem value="LOCATED_IN">Located In</SelectItem>
                <SelectItem value="OWNS">Owns</SelectItem>
                <SelectItem value="PARTNER_OF">Partner Of</SelectItem>
                <SelectItem value="SUBSIDIARY_OF">Subsidiary Of</SelectItem>
                <SelectItem value="MANUFACTURES">Manufactures</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Relationships Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Relationships ({relationships?.length})</CardTitle>
              <CardDescription>
                Complete list of knowledge graph relationships
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus size={16} className="mr-2" />
                Add Relationship
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <DataTable data={relationships} columns={relationshipColumns} />
        </CardContent>
      </Card>

      {/* Create Relationship Dialog */}
      <Dialog
        title="Create New Relationship"
        description="Add a new relationship between entities"
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Relationship Type</label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select relationship type..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="WORKS_FOR">Works For</SelectItem>
                <SelectItem value="LOCATED_IN">Located In</SelectItem>
                <SelectItem value="OWNS">Owns</SelectItem>
                <SelectItem value="PARTNER_OF">Partner Of</SelectItem>
                <SelectItem value="SUBSIDIARY_OF">Subsidiary Of</SelectItem>
                <SelectItem value="MANUFACTURES">Manufactures</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Source Entity</label>
            <Input placeholder="Search for source entity..." className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Target Entity</label>
            <Input placeholder="Search for target entity..." className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Properties (JSON)</label>
            <Textarea
              className="mt-1"
              rows={3}
              placeholder='{"start_date": "2023-01-01", "position": "CEO"}'
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch id="verified" />
            <label htmlFor="verified" className="text-sm font-medium">
              Mark as verified
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button>Create Relationship</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
