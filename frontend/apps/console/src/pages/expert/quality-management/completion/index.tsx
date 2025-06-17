import React, { useCallback,  useState } from 'react';
import { toast } from 'sonner';
import * as z from 'zod';

// UI Components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';


// Form Schema
const completionFormSchema = z.object({
  completion_types: z.array(z.string()).min(1, "Chọn ít nhất một loại completion"),
  auto_apply_suggestions: z.boolean().default(false),
  confidence_threshold: z.number().min(0).max(1).default(0.8),
  limit_entities: z.number().optional(),
  limit_relationships: z.number().optional(),
});

// Custom Components
import StatisticCard from '@/components/statistic-card';

// Icons
import { 
  Sparkles, 
  Brain, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Eye,
  Trash2,
  RefreshCw,
  TrendingUp,
  Network,
  Users,
  Link2,
  Bot,
  X
} from 'lucide-react';

// Import hooks
import {
  useKGCompletionSuggestions,
  useKGCompletionStats,
  useGenerateKGCompletion,
  useHandleSuggestionAction,
  useDeleteSuggestion,
  useSuggestionFilters,
  useBulkSuggestionSelection,
} from '@vbkg/api-client';

// Types
import {
  ICompletionSuggestion,
  IKGCompletionStats,
  IKGCompletionRequest,
  ISuggestionActionRequest,
} from '@vbkg/types';
import { ActionButton, DataTable, FieldConfig, SimpleColumnDef } from '@/components';
import DialogComponent from '@/components/custom-dialog';
import GeneralForm from '@/components/form';
import SuggestionDetailModal from './components/SuggestionDetailModal';


const KnowledgeGraphCompletionPage: React.FC = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<ICompletionSuggestion | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Use custom hooks for filters and selection
  const { filters, updateFilter, resetFilters } = useSuggestionFilters();
  const { 
    selectedIds, 
    toggleSuggestion, 
    clearSelection, 
    hasSelection, 
    selectionCount 
  } = useBulkSuggestionSelection();

  // Queries using custom hooks
  const { 
    data: statsResponse, 
    isLoading: statsLoading 
  } = useKGCompletionStats({
    refetchInterval: 30000,
  });

  const { 
    data: suggestionsResponse, 
    isLoading: suggestionsLoading, 
    refetch: refetchSuggestions 
  } = useKGCompletionSuggestions(filters);

  // Mutations using custom hooks
  const generateCompletionMutation = useGenerateKGCompletion({
    onSuccess: () => {
      toast.success('Knowledge graph completion hoàn thành!');
    },
    onError: (error: any) => {
      toast.error(`Lỗi: ${error.message}`);
    },
    onSettled: () => {
      setIsGenerating(false);
    },
  });

  const suggestionActionMutation = useHandleSuggestionAction({
    onSuccess: (data) => {
      toast.success(data.data.message);
      clearSelection();
    },
    onError: (error: any) => {
      toast.error(`Lỗi: ${error.message}`);
    },
  });

  const deleteSuggestionMutation = useDeleteSuggestion({
    onSuccess: () => {
      toast.success('Đã xóa suggestion');
    },
    onError: (error: any) => {
      toast.error(`Lỗi: ${error.message}`);
    },
  });

  // Form configuration
  const completionFormFields: FieldConfig[] = [
    {
      name: 'completion_types',
      label: 'Loại Completion',
      type: 'checkbox',
      required: true,
      options: [
        { label: 'Entities thiếu', value: 'missing_entities' },
        { label: 'Relationships thiếu', value: 'missing_relationships' },
      ],
      description: 'Chọn loại completion muốn thực hiện',
      defaultValue: ['missing_entities', 'missing_relationships'],
    },
    {
      name: 'auto_apply_suggestions',
      label: 'Tự động áp dụng suggestions có confidence cao',
      type: 'switch',
      description: 'Tự động tạo entities/relationships từ suggestions có confidence >= threshold',
      defaultValue: false,
    },
    {
      name: 'confidence_threshold',
      label: 'Confidence Threshold',
      type: 'number',
      placeholder: '0.8',
      description: 'Ngưỡng confidence tối thiểu để tự động áp dụng (0.0 - 1.0)',
      defaultValue: 0.8,
    },
    {
      name: 'limit_entities',
      label: 'Giới hạn số entities phân tích',
      type: 'number',
      placeholder: '1000',
      description: 'Để trống để phân tích tất cả entities',
    },
    {
      name: 'limit_relationships',
      label: 'Giới hạn số relationships phân tích',
      type: 'number',
      placeholder: '1000',
      description: 'Để trống để phân tích tất cả relationships',
    },
  ];

  // Table columns
  const suggestionColumns: SimpleColumnDef<ICompletionSuggestion, any>[] = [
    {
      header: 'Loại',
      accessorKey: 'suggestion_type',
      cell: (row) => (
        <Badge variant={row?.suggestion_type === 'entity' ? 'default' : 'secondary'}>
          {row?.suggestion_type === 'entity' ? (
            <>
              <Users className="w-3 h-3 mr-1" />
              Entity
            </>
          ) : (
            <>
              <Link2 className="w-3 h-3 mr-1" />
              Relationship
            </>
          )}
        </Badge>
      ),
    },
    {
      header: 'Nội dung',
      accessorFn: (row) => row.suggestion_type === 'entity' 
        ? row.suggested_entity_text 
        : `${row.source_entity_text} → ${row.target_entity_text}`,
      cell: (row) => (
        <div className="max-w-md">
          {row?.suggestion_type === 'entity' ? (
            <div>
              <div className="font-medium">{row.suggested_entity_text}</div>
              <div className="text-sm text-muted-foreground">{row.suggested_entity_type}</div>
            </div>
          ) : (
            <div>
              <div className="font-medium">{row.suggested_relationship_type}</div>
              <div className="text-sm text-muted-foreground">
                {row.source_entity_text} → {row.target_entity_text}
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      header: 'Confidence',
      accessorKey: 'confidence',
      cell: (row) => (
        <div className="text-center">
          <div className="text-sm font-medium">
            {(row?.confidence * 100).toFixed(1)}%
          </div>
          <Progress 
            value={row?.confidence * 100} 
            className="w-16 h-2 mt-1"
          />
        </div>
      ),
    },
    {
      header: 'Ưu tiên',
      accessorKey: 'priority',
      cell: (row) => {
        const priorityColors = {
          low: 'bg-gray-100 text-gray-800',
          medium: 'bg-blue-100 text-blue-800',
          high: 'bg-orange-100 text-orange-800',
          critical: 'bg-red-100 text-red-800',
        };
        return (
          <Badge className={priorityColors[row?.priority as keyof typeof priorityColors]}>
            {row?.priority}
          </Badge>
        );
      },
    },
    {
      header: 'Trạng thái',
      accessorKey: 'status',
      cell: (row) => {
        const statusConfig = {
          pending: { label: 'Đang chờ', icon: Clock, color: 'bg-yellow-100 text-yellow-800' },
          accepted: { label: 'Đã chấp nhận', icon: CheckCircle, color: 'bg-green-100 text-green-800' },
          rejected: { label: 'Đã từ chối', icon: XCircle, color: 'bg-red-100 text-red-800' },
          applied: { label: 'Đã áp dụng', icon: CheckCircle, color: 'bg-blue-100 text-blue-800' },
        };
        const config = statusConfig[row?.status as keyof typeof statusConfig];
        const Icon = config?.icon || Clock;
        
        return (
          <Badge className={config?.color}>
            <Icon className="w-3 h-3 mr-1" />
            {config?.label}
          </Badge>
        );
      },
    },
    {
      header: 'Lý do',
      accessorKey: 'reason',
      cell: (row) => (
        <div className="max-w-xs text-sm text-muted-foreground truncate" title={row?.reason}>
          {row?.reason}
        </div>
      ),
    },
    {
      header: 'Nguồn',
      accessorKey: 'source',
      cell: (row) => (
        <Badge variant="outline" className="text-xs">
          {row?.source}
        </Badge>
      ),
    },
  ];

  // Table actions
  const suggestionActions: ActionButton<ICompletionSuggestion>[] = [
    {
      label: 'Xem chi tiết',
      icon: <Eye className="w-4 h-4" />,
      onClick: (row) => {
        setSelectedSuggestion(row);
        setShowDetailModal(true);
      },
      variant: 'ghost',
    },
    {
      label: 'Xóa',
      icon: <Trash2 className="w-4 h-4" />,
      onClick: (row) => {
        if (confirm('Bạn có chắc muốn xóa suggestion này?')) {
          deleteSuggestionMutation.mutate(row.id);
        }
      },
      variant: 'ghost',
    },
  ];

  // Handle form submission
  const handleGenerateCompletion = (data: z.infer<typeof completionFormSchema>) => {
    setIsGenerating(true);
    generateCompletionMutation.mutate(data as IKGCompletionRequest);
  };

  // Handle bulk actions
  const handleBulkAction = (action: string, reviewNotes?: string, rejectionReason?: string) => {
    if (selectedIds.length === 0) {
      toast.error('Vui lòng chọn ít nhất một suggestion');
      return;
    }

    const actionRequest: ISuggestionActionRequest = {
      suggestion_ids: selectedIds,
      action: action as 'accept' | 'reject' | 'apply',
      review_notes: reviewNotes,
      rejection_reason: rejectionReason,
    };

    suggestionActionMutation.mutate(actionRequest);
  };

  // Handle single suggestion action from detail modal
  const handleSuggestionAction = (action: 'accept' | 'reject' | 'apply', suggestion: ICompletionSuggestion) => {
    const actionRequest: ISuggestionActionRequest = {
      suggestion_ids: [suggestion.id],
      action,
    };

    suggestionActionMutation.mutate(actionRequest, {
      onSuccess: () => {
        setShowDetailModal(false);
        setSelectedSuggestion(null);
      },
    });
  };

  // Handle row selection
  const handleRowSelection = useCallback((rows: ICompletionSuggestion[]) => {
    // Clear current selection and set new selection
    clearSelection();
    rows.forEach(row => toggleSuggestion(row.id));
  }, [clearSelection, toggleSuggestion]);

  // Handle filter changes
  const handleFilterChange = (key: string, value: any) => {
    updateFilter(key as any, value);
  };

  // Extract data from API responses
  const stats = statsResponse?.data;
  const suggestions = suggestionsResponse?.data || [];
  const total = suggestionsResponse?.meta?.total || 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="w-8 h-8 text-blue-600" />
            Knowledge Graph Completion
          </h1>
          <p className="text-muted-foreground mt-2">
            Tự động hoàn thiện knowledge graph bằng AI suggestions
          </p>
        </div>
        
        <DialogComponent
          title="Tạo Knowledge Graph Completion"
          description="Cấu hình và chạy completion để tự động gợi ý entities và relationships thiếu"
          customTrigger={
            <Button size="lg" className="gap-2" disabled={isGenerating}>
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Đang tạo...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Tạo Completion
                </>
              )}
            </Button>
          }
          size="lg"
        >
          <GeneralForm
            schema={completionFormSchema}
            fields={completionFormFields}
            onSubmit={handleGenerateCompletion}
            submitButtonText={isGenerating ? "Đang tạo..." : "Tạo Completion"}
            isLoading={isGenerating}
          />
        </DialogComponent>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatisticCard
          title="Tổng suggestions"
          value={stats?.total_suggestions || 0}
          icon={<Bot className="w-5 h-5" />}
          color="blue"
          loading={statsLoading}
        />
        <StatisticCard
          title="Đang chờ xử lý"
          value={stats?.pending_suggestions || 0}
          icon={<Clock className="w-5 h-5" />}
          color="yellow"
          loading={statsLoading}
        />
        <StatisticCard
          title="Đã áp dụng"
          value={stats?.applied_suggestions || 0}
          icon={<CheckCircle className="w-5 h-5" />}
          color="green"
          loading={statsLoading}
        />
        <StatisticCard
          title="Confidence trung bình"
          value={stats ? `${(stats.avg_confidence * 100).toFixed(1)}%` : '0%'}
          icon={<TrendingUp className="w-5 h-5" />}
          color="purple"
          loading={statsLoading}
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="w-5 h-5" />
              Phân bố theo loại
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Entity suggestions</span>
                <Badge variant="default">{stats?.entity_suggestions || 0}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Relationship suggestions</span>
                <Badge variant="secondary">{stats?.relationship_suggestions || 0}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Cần chú ý
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Ưu tiên cao đang chờ</span>
                <Badge variant="destructive">{stats?.high_priority_pending || 0}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Đã từ chối</span>
                <Badge variant="outline">{stats?.rejected_suggestions || 0}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="suggestions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="suggestions" className="space-y-4">
          {/* Bulk Actions */}
          {hasSelection && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>Đã chọn {selectionCount} suggestions</span>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleBulkAction('accept')}
                    disabled={suggestionActionMutation.isPending}
                  >
                    Chấp nhận
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleBulkAction('reject')}
                    disabled={suggestionActionMutation.isPending}
                  >
                    Từ chối
                  </Button>
                  <Button 
                    size="sm"
                    onClick={() => handleBulkAction('apply')}
                    disabled={suggestionActionMutation.isPending}
                  >
                    Áp dụng
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Trạng thái:</span>
                  <select 
                    value={filters.status || 'all'} 
                    onChange={(e) => handleFilterChange('status', e.target.value === 'all' ? undefined : e.target.value)}
                    className="px-3 py-1 border rounded-md text-sm"
                  >
                    <option value="all">Tất cả</option>
                    <option value="pending">Đang chờ</option>
                    <option value="accepted">Đã chấp nhận</option>
                    <option value="rejected">Đã từ chối</option>
                    <option value="applied">Đã áp dụng</option>
                  </select>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Loại:</span>
                  <select 
                    value={filters.suggestion_type || 'all'} 
                    onChange={(e) => handleFilterChange('suggestion_type', e.target.value === 'all' ? undefined : e.target.value)}
                    className="px-3 py-1 border rounded-md text-sm"
                  >
                    <option value="all">Tất cả</option>
                    <option value="entity">Entity</option>
                    <option value="relationship">Relationship</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Ưu tiên:</span>
                  <select 
                    value={filters.priority || 'all'} 
                    onChange={(e) => handleFilterChange('priority', e.target.value === 'all' ? undefined : e.target.value)}
                    className="px-3 py-1 border rounded-md text-sm"
                  >
                    <option value="all">Tất cả</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => refetchSuggestions()}
                  className="ml-auto"
                  disabled={suggestionsLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${suggestionsLoading ? 'animate-spin' : ''}`} />
                  Làm mới
                </Button>

                {(filters.status || filters.suggestion_type || filters.priority) && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={resetFilters}
                    className="text-destructive border-destructive hover:bg-destructive/10"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Xóa bộ lọc
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Suggestions Table */}
          <Card>
            <CardContent className="pt-6">
              <DataTable
                data={suggestions}
                columns={suggestionColumns}
                showRowSelection={true}
                onRowSelectionChange={handleRowSelection}
                actionsOptions={{
                  show: true,
                  actions: suggestionActions,
                  showInDropdown: true,
                }}
                showGlobalFilter={true}
                showPagination={true}
                defaultPageSize={20}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Xu hướng theo thời gian</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-center py-8">
                  Biểu đồ xu hướng sẽ được triển khai ở version sau
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Phân tích chất lượng</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Confidence trung bình</span>
                      <span>{stats ? `${(stats.avg_confidence * 100).toFixed(1)}%` : '0%'}</span>
                    </div>
                    <Progress value={stats ? stats.avg_confidence * 100 : 0} />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Tỷ lệ được chấp nhận</span>
                      <span>
                        {stats && stats.total_suggestions > 0 
                          ? `${((stats.accepted_suggestions + stats.applied_suggestions) / stats.total_suggestions * 100).toFixed(1)}%`
                          : '0%'
                        }
                      </span>
                    </div>
                    <Progress 
                      value={stats && stats.total_suggestions > 0 
                        ? (stats.accepted_suggestions + stats.applied_suggestions) / stats.total_suggestions * 100
                        : 0
                      } 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Suggestion Detail Modal */}
      <SuggestionDetailModal
        suggestion={selectedSuggestion}
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedSuggestion(null);
        }}
        onAction={handleSuggestionAction}
        isLoading={suggestionActionMutation.isPending}
      />
    </div>
  );
};

export default KnowledgeGraphCompletionPage;
