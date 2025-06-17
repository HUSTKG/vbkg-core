import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Users, 
  Link2, 
  Calendar, 
  User, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  Eye,
  Brain,
  Target,
  Zap
} from 'lucide-react';
import { ICompletionSuggestion } from '@vbkg/types';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';
import DialogComponent from '@/components/custom-dialog';

interface SuggestionDetailModalProps {
  suggestion: ICompletionSuggestion | null;
  isOpen: boolean;
  onClose: () => void;
  onAction?: (action: 'accept' | 'reject' | 'apply', suggestion: ICompletionSuggestion) => void;
  isLoading?: boolean;
}

const SuggestionDetailModal: React.FC<SuggestionDetailModalProps> = ({
  suggestion,
  isOpen,
  onClose,
  onAction,
  isLoading = false,
}) => {
  if (!suggestion) return null;

  const statusConfig = {
    pending: { label: 'Đang chờ', icon: Clock, color: 'bg-yellow-100 text-yellow-800' },
    accepted: { label: 'Đã chấp nhận', icon: CheckCircle, color: 'bg-green-100 text-green-800' },
    rejected: { label: 'Đã từ chối', icon: XCircle, color: 'bg-red-100 text-red-800' },
    applied: { label: 'Đã áp dụng', icon: CheckCircle, color: 'bg-blue-100 text-blue-800' },
  };

  const priorityColors = {
    low: 'bg-gray-100 text-gray-800',
    medium: 'bg-blue-100 text-blue-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };

  const config = statusConfig[suggestion.status];
  const StatusIcon = config.icon;

  const renderSuggestionContent = () => {
    if (suggestion.suggestion_type === 'entity') {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Entity Suggestion
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Entity Text</label>
                <p className="text-lg font-semibold">{suggestion.suggested_entity_text}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Entity Type</label>
                <Badge variant="outline" className="mt-1">
                  {suggestion.suggested_entity_type}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            Relationship Suggestion
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Relationship Type</label>
            <p className="text-lg font-semibold">{suggestion.suggested_relationship_type}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Source Entity</label>
              <p className="font-medium">{suggestion.source_entity_text}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">Target Entity</label>
              <p className="font-medium">{suggestion.target_entity_text}</p>
            </div>
          </div>

          <div className="flex items-center justify-center py-2">
            <div className="flex items-center space-x-2">
              <div className="px-3 py-1 bg-blue-50 rounded-md text-blue-700 font-medium">
                {suggestion.source_entity_text}
              </div>
              <div className="text-muted-foreground">→</div>
              <div className="px-2 py-1 bg-green-50 rounded text-green-700 text-sm">
                {suggestion.suggested_relationship_type}
              </div>
              <div className="text-muted-foreground">→</div>
              <div className="px-3 py-1 bg-purple-50 rounded-md text-purple-700 font-medium">
                {suggestion.target_entity_text}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderMetadata = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="w-4 h-4" />
            Confidence & Priority
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Confidence Score</span>
              <span className="text-sm font-bold">{(suggestion.confidence * 100).toFixed(1)}%</span>
            </div>
            <Progress value={suggestion.confidence * 100} className="h-2" />
          </div>
          
          <div>
            <label className="text-sm font-medium text-muted-foreground">Priority Level</label>
            <div className="mt-1">
              <Badge className={priorityColors[suggestion.priority]}>
                {suggestion.priority.toUpperCase()}
              </Badge>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">Source</label>
            <div className="mt-1">
              <Badge variant="outline">
                {suggestion.source}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="w-4 h-4" />
            Status & Timeline
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Current Status</label>
            <div className="mt-1">
              <Badge className={config.color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {config.label}
              </Badge>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">Created At</label>
            <p className="text-sm mt-1">
              {format(new Date(suggestion.created_at), 'PPpp', { locale: vi })}
            </p>
          </div>

          {suggestion.applied_at && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Applied At</label>
              <p className="text-sm mt-1">
                {format(new Date(suggestion.applied_at), 'PPpp', { locale: vi })}
              </p>
            </div>
          )}

          {suggestion.reviewed_at && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Reviewed At</label>
              <p className="text-sm mt-1">
                {format(new Date(suggestion.reviewed_at), 'PPpp', { locale: vi })}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const renderReasonAndContext = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="w-4 h-4" />
          Reasoning & Context
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Reason</label>
          <p className="mt-1 text-sm leading-relaxed bg-gray-50 p-3 rounded-md">
            {suggestion.reason}
          </p>
        </div>

        {suggestion.context_data && Object.keys(suggestion.context_data).length > 0 && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Context Data</label>
            <pre className="mt-1 text-xs bg-gray-50 p-3 rounded-md overflow-auto max-h-32">
              {JSON.stringify(suggestion.context_data, null, 2)}
            </pre>
          </div>
        )}

        {suggestion.review_notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Review Notes</label>
            <p className="mt-1 text-sm leading-relaxed bg-blue-50 p-3 rounded-md">
              {suggestion.review_notes}
            </p>
          </div>
        )}

        {suggestion.rejection_reason && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Rejection Reason</label>
            <p className="mt-1 text-sm leading-relaxed bg-red-50 p-3 rounded-md">
              {suggestion.rejection_reason}
            </p>
          </div>
        )}

        {suggestion.validation_errors && Object.keys(suggestion.validation_errors).length > 0 && (
          <div>
            <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              Validation Errors
            </label>
            <pre className="mt-1 text-xs bg-orange-50 p-3 rounded-md overflow-auto max-h-32">
              {JSON.stringify(suggestion.validation_errors, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderActions = () => {
    if (suggestion.status === 'applied') {
      return null; // No actions available for applied suggestions
    }

    const isPending = suggestion.status === 'pending';
    const isAccepted = suggestion.status === 'accepted';

    return (
      <div className="flex flex-wrap gap-2 justify-end">
        {isPending && (
          <>
            <Button
              variant="outline"
              onClick={() => onAction?.('accept', suggestion)}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Chấp nhận
            </Button>
            <Button
              variant="outline"
              onClick={() => onAction?.('reject', suggestion)}
              disabled={isLoading}
              className="flex items-center gap-2 text-red-600 border-red-300 hover:bg-red-50"
            >
              <XCircle className="w-4 h-4" />
              Từ chối
            </Button>
          </>
        )}
        
        {(isPending || isAccepted) && (
          <Button
            onClick={() => onAction?.('apply', suggestion)}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <Zap className="w-4 h-4" />
            Áp dụng
          </Button>
        )}
      </div>
    );
  };

  return (
    <DialogComponent
      title={`Chi tiết Suggestion`}
      description={`${suggestion.suggestion_type === 'entity' ? 'Entity' : 'Relationship'} suggestion với confidence ${(suggestion.confidence * 100).toFixed(1)}%`}
      open={isOpen}
      onOpenChange={(open) => !open && onClose()}
      size="3xl"
    >
      <div className="space-y-6">
        {/* Main Content */}
        {renderSuggestionContent()}

        {/* Metadata */}
        {renderMetadata()}

        {/* Reason and Context */}
        {renderReasonAndContext()}

        <Separator />

        {/* Actions */}
        {renderActions()}
      </div>
    </DialogComponent>
  );
};

export default SuggestionDetailModal;
