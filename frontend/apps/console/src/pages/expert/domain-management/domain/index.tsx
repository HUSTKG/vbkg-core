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
} from "@vbkg/ui";
import CreateDomainDialog from "./dialog/create";
import { useCreateDomain, useDomains, useDomainStats } from "@vbkg/api-client";
import { CreateDomainSchema } from "@vbkg/schemas";
import DomainListTable from "./table/list-domain";

const mockStats = {
  total_domains: 4,
  total_entity_types: 23,
  total_relationship_types: 15,
  active_domains: 3,
};

const DomainManagementPage: React.FC = () => {
  const { data: domainResponse } = useDomains({
    limit: 100,
  });

  const domains = domainResponse?.data || [];

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

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
          value={mockStats.total_domains}
          icon={<Database size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Entity Types"
          value={mockStats.total_entity_types}
          icon={<Settings size={20} />}
          color="green"
        />
        <StatisticCard
          title="Relationship Types"
          value={mockStats.total_relationship_types}
          icon={<BarChart3 size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Domain Hoạt Động"
          value={mockStats.active_domains}
          icon={<Database size={20} />}
          color="orange"
        />
      </div>

      {/* Main Content */}
      <Tabs defaultValue="domains" className="space-y-4">
        <TabsList>
          <TabsTrigger value="domains">Danh Sách Domain</TabsTrigger>
          <TabsTrigger value="analytics">Thống Kê</TabsTrigger>
        </TabsList>

        <TabsContent value="domains" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Danh Sách Domain</CardTitle>
            </CardHeader>
            <CardContent>
              <DomainListTable domains={domains} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Domain Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {domains.map((domain) => (
                    <div
                      key={domain.id}
                      className="flex justify-between items-center p-3 border rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: domain.color }}
                        />
                        <div>
                          <p className="font-medium">{domain.display_name}</p>
                          <p className="text-sm text-gray-500">{domain.name}</p>
                        </div>
                      </div>
                      <Badge
                        variant={domain.is_active ? "default" : "secondary"}
                      >
                        {domain.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="text-sm text-gray-500 text-center py-8">
                    Chưa có hoạt động gần đây
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

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
