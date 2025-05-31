import React, { useState } from "react";
import { Database, Settings, Download, FileText, Search } from "lucide-react";
import * as z from "zod";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  StatisticCard,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@vbkg/ui";
import { useFiboClasses, useFiboProperties } from "@vbkg/api-client";
import { ImportOntologySchema } from "@vbkg/schemas";
import PropertyListTable from "./table/property-list";
import ClassListTable from "./table/class-list";
import ImportOntologyDialog from "./dialog/import";
import CreateFiboPropertyDialog from "./dialog/create-property";
import CreateFiboClassDialog from "./dialog/create-class";

const FIBOManagementPage: React.FC = () => {
  const { data: fiboClassResponse } = useFiboClasses({
    limit: 200,
  });
  const fiboClasses = fiboClassResponse?.data || [];

  const { data: fiboPropertyResponse } = useFiboProperties({
    limit: 200,
  });

  const fiboProperties = fiboPropertyResponse?.data || [];

  // Modal states
  const [isCreateClassModalOpen, setIsCreateClassModalOpen] = useState(false);
  const [isCreatePropertyModalOpen, setIsCreatePropertyModalOpen] =
    useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  const [importProgress, setImportProgress] = useState(0);

  // Filters
  const [classFilters, setClassFilters] = useState({
    domain: "all",
    is_custom: "all",
    search: "",
  });
  const [propertyFilters, setPropertyFilters] = useState({
    property_type: "all",
    is_custom: "all",
    search: "",
  });

  // Helper functions
  const getClassByUri = (uri: string) => fiboClasses.find((c) => c.uri === uri);
  const getClassById = (id: number) => fiboClasses.find((c) => c.id === id);

  const getDomains = () => {
    const domains = new Set(fiboClasses.map((c) => c.domain).filter(Boolean));
    return Array.from(domains);
  };

  // Form fields for FIBO Class

  // Filtered data
  const filteredClasses = fiboClasses.filter((c) => {
    if (classFilters.domain !== "all" && c.domain !== classFilters.domain)
      return false;
    if (
      classFilters.is_custom !== "all" &&
      c.is_custom.toString() !== classFilters.is_custom
    )
      return false;
    if (
      classFilters.search &&
      !c.label?.toLowerCase().includes(classFilters.search.toLowerCase()) &&
      !c.uri.toLowerCase().includes(classFilters.search.toLowerCase())
    )
      return false;
    return true;
  });

  const filteredProperties = fiboProperties.filter((p) => {
    if (
      propertyFilters.property_type !== "all" &&
      p.property_type !== propertyFilters.property_type
    )
      return false;
    if (
      propertyFilters.is_custom !== "all" &&
      p.is_custom.toString() !== propertyFilters.is_custom
    )
      return false;
    if (
      propertyFilters.search &&
      !p.label?.toLowerCase().includes(propertyFilters.search.toLowerCase()) &&
      !p.uri.toLowerCase().includes(propertyFilters.search.toLowerCase())
    )
      return false;
    return true;
  });

  // Statistics
  const stats = {
    totalClasses: fiboClasses.length,
    customClasses: fiboClasses.filter((c) => c.is_custom).length,
    totalProperties: fiboProperties.length,
    objectProperties: fiboProperties.filter((p) => p.property_type === "object")
      .length,
    datatypeProperties: fiboProperties.filter(
      (p) => p.property_type === "datatype",
    ).length,
    customProperties: fiboProperties.filter((p) => p.is_custom).length,
    domains: getDomains().length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            FIBO Ontology Management
          </h1>
          <p className="text-gray-600 mt-1">
            Quản lý FIBO classes, properties và import ontology
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setIsImportModalOpen(true)}>
            Import Ontology
          </Button>
          <Button>
            <Download size={16} className="mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatisticCard
          title="Total Classes"
          value={stats.totalClasses}
          icon={<Database size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Custom Classes"
          value={stats.customClasses}
          icon={<Settings size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Total Properties"
          value={stats.totalProperties}
          icon={<FileText size={20} />}
          color="green"
        />
        <StatisticCard
          title="Object Properties"
          value={stats.objectProperties}
          icon={<FileText size={20} />}
          color="orange"
        />
        <StatisticCard
          title="Datatype Properties"
          value={stats.datatypeProperties}
          icon={<FileText size={20} />}
          color="teal"
        />
        <StatisticCard
          title="Custom Properties"
          value={stats.customProperties}
          icon={<Settings size={20} />}
          color="pink"
        />
        <StatisticCard
          title="Domains"
          value={stats.domains}
          icon={<Database size={20} />}
          color="indigo"
        />
      </div>

      {/* Main Content */}
      <Tabs defaultValue="classes" className="space-y-4">
        <TabsList>
          <TabsTrigger value="classes">FIBO Classes</TabsTrigger>
          <TabsTrigger value="properties">FIBO Properties</TabsTrigger>
          <TabsTrigger value="hierarchy">Class Hierarchy</TabsTrigger>
        </TabsList>

        <TabsContent value="classes" className="space-y-4">
          {/* Class Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Search</label>
                  <div className="relative mt-1">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search classes..."
                      value={classFilters.search}
                      onChange={(e) =>
                        setClassFilters((prev) => ({
                          ...prev,
                          search: e.target.value,
                        }))
                      }
                      className="pl-8"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Domain</label>
                  <Select
                    value={classFilters.domain}
                    onValueChange={(value) =>
                      setClassFilters((prev) => ({ ...prev, domain: value }))
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Domains</SelectItem>
                      {getDomains().map((domain) => (
                        <SelectItem key={domain} value={domain}>
                          {domain}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Type</label>
                  <Select
                    value={classFilters.is_custom}
                    onValueChange={(value) =>
                      setClassFilters((prev) => ({ ...prev, is_custom: value }))
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="false">FIBO Standard</SelectItem>
                      <SelectItem value="true">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end">
                  <Button onClick={() => setIsCreateClassModalOpen(true)}>
                    Create Class
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>FIBO Classes ({filteredClasses.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ClassListTable
                classes={filteredClasses}
                getClassById={getClassById}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="properties" className="space-y-4">
          {/* Property Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Search</label>
                  <div className="relative mt-1">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search properties..."
                      value={propertyFilters.search}
                      onChange={(e) =>
                        setPropertyFilters((prev) => ({
                          ...prev,
                          search: e.target.value,
                        }))
                      }
                      className="pl-8"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Property Type</label>
                  <Select
                    value={propertyFilters.property_type}
                    onValueChange={(value) =>
                      setPropertyFilters((prev) => ({
                        ...prev,
                        property_type: value,
                      }))
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="object">Object Property</SelectItem>
                      <SelectItem value="datatype">
                        Datatype Property
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Source</label>
                  <Select
                    value={propertyFilters.is_custom}
                    onValueChange={(value) =>
                      setPropertyFilters((prev) => ({
                        ...prev,
                        is_custom: value,
                      }))
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sources</SelectItem>
                      <SelectItem value="false">FIBO Standard</SelectItem>
                      <SelectItem value="true">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end">
                  <Button onClick={() => setIsCreatePropertyModalOpen(true)}>
                    Create Property
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                FIBO Properties ({filteredProperties.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <PropertyListTable
                getClassById={getClassById}
                fiboClasses={fiboClasses}
                properties={filteredProperties}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hierarchy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Class Hierarchy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {fiboClasses
                  .filter((c) => !c.parent_class_id)
                  .map((rootClass) => (
                    <div key={rootClass.id} className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <Database className="h-4 w-4 text-blue-600" />
                        <span className="font-medium">
                          {rootClass.label || rootClass.uri}
                        </span>
                        <Badge variant="outline">{rootClass.domain}</Badge>
                      </div>

                      {/* Child classes */}
                      <div className="ml-6 space-y-2">
                        {fiboClasses
                          .filter((c) => c.parent_class_id === rootClass.id)
                          .map((childClass) => (
                            <div
                              key={childClass.id}
                              className="flex items-center space-x-2 text-sm"
                            >
                              <span className="text-gray-400">└─</span>
                              <span>{childClass.label || childClass.uri}</span>
                              <Badge variant="outline" className="text-xs">
                                {childClass.domain}
                              </Badge>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Property Modal */}
      <ImportOntologyDialog
        isImportModalOpen={isImportModalOpen}
        setIsImportModalOpen={setIsImportModalOpen}
        importProgress={importProgress}
      />
      <CreateFiboPropertyDialog
        isCreatePropertyModalOpen={isCreatePropertyModalOpen}
        setIsCreatePropertyModalOpen={setIsCreatePropertyModalOpen}
        fiboClasses={fiboClasses}
      />
      <CreateFiboClassDialog
        isCreateClassModalOpen={isCreateClassModalOpen}
        setIsCreateClassModalOpen={setIsCreateClassModalOpen}
        fiboClasses={fiboClasses}
      />
    </div>
  );
};

export default FIBOManagementPage;
