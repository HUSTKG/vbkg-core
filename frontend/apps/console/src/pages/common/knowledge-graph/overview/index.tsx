import { useKGStats } from "@vbkg/api-client";
import {
    Badge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    StatisticCard,
} from "@/components";
import { Database, GitBranch, Layers, Network, RefreshCw } from "lucide-react";

export default function KnowledgeGraphOverview() {
  const { data: stats, isFetching: loading } = useKGStats();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">📊 Knowledge Graph Overview</h1>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => window.location.reload()}>
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <StatisticCard
          title="Total Entities"
          value={loading ? "..." : stats?.total_entities?.toLocaleString() || 0}
          icon={<Database size={20} />}
          color="blue"
          loading={loading}
        />
        <StatisticCard
          title="Total Relationships"
          value={
            loading ? "..." : stats?.total_relationships?.toLocaleString() || 0
          }
          icon={<Network size={20} />}
          color="green"
          loading={loading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Entity Types Distribution */}
        <Card className="lg:col-span-1 overflow-y-auto max-h-[60vh]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers size={20} />
              Entity Types
            </CardTitle>
            <CardDescription>Distribution by entity type</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex justify-between items-center">
                    <div className="h-4 bg-muted rounded w-24 animate-pulse" />
                    <div className="h-4 bg-muted rounded w-12 animate-pulse" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {stats?.entity_types?.map((type, i) => (
                  <div key={String(i)} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Badge variant="outline">{type.type}</Badge>
                      <span className="font-medium">
                        {type.count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{
                          width: `${(type.count / stats.total_entities) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Relationship Types Distribution */}
        <Card className="lg:col-span-1 overflow-y-auto p-0 max-h-[60vh]">
          <CardHeader className="sticky top-0 bg-white/95 p-4">
            <CardTitle className="flex items-center gap-2">
              <GitBranch size={20} />
              Relationship Types
            </CardTitle>
            <CardDescription>Distribution by relationship type</CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex justify-between items-center">
                    <div className="h-4 bg-muted rounded w-28 animate-pulse" />
                    <div className="h-4 bg-muted rounded w-12 animate-pulse" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {stats?.relationship_types?.map((type, i) => (
                  <div key={String(i)} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Badge variant="secondary">
                        {type.type}
                      </Badge>
                      <span className="font-medium">
                        {type.count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{
                          width: `${(type.count / stats.total_relationships) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
