// Utility
export * from "@/lib/utils";

// Data Display Components
export { default as EntityCard } from "@/components/entity-card";
export type {
  EntityCardProps,
  EntityProperty,
  EntityRelation,
} from "@/components/entity-card";

export { default as ResultCard } from "@/components/result-card";
export type {
  ResultCardProps,
  ResultProperty,
  ResultRelation,
} from "@/components/result-card";

export {
  default as StatisticCard,
  NodeStatisticCard,
  RelationStatisticCard,
  ConflictStatisticCard,
  UserStatisticCard,
} from "@/components/statistic-card";
export type { StatisticCardProps } from "@/components/statistic-card";

// Activity and Notification Components
export {
  default as RecentActivityItem,
  formatTimeAgo,
  DataAddedActivity,
  ConflictDetectedActivity,
  ErrorActivity,
  InfoActivity,
} from "@/components/recent-activity-item";
export type {
  RecentActivityItemProps,
  ActivityStatus,
} from "@/components/recent-activity-item";

export {
  default as NotificationItem,
  SuccessNotification,
  WarningNotification,
  ErrorNotification,
  InfoNotification,
} from "@/components/notification-item";
export type {
  NotificationItemProps,
  NotificationType,
} from "@/components/notification-item";

// Ontology Components
export { default as OntologyGraph } from "@/components/ontology-graph";
export type {
  OntologyGraphProps,
  OntologyClass as OntologyGraphClass,
  OntologyRelation as OntologyGraphRelation,
} from "@/components/ontology-graph";

export { default as ClassDetails } from "@/components/class-details";
export type {
  ClassDetailsProps,
  OntologyClass,
  OntologyProperty,
} from "@/components/class-details";

// Search, Navigation, and User Interface Components
export { default as SearchBar } from "@/components/search-bar";
export type { SearchBarProps, SearchHistory } from "@/components/search-bar";

export { default as UserDropdown } from "@/components/user-dropdown";
export type {
  UserDropdownProps,
  UserMenuLink,
} from "@/components/user-dropdown";

export {
  SidebarMenu,
  SidebarMenuItem,
  SidebarSubItem,
  SidebarHomeItem,
} from "@/components/sidebar-menu";
export type {
  SidebarMenuProps,
  SidebarMenuItemProps,
  SidebarSubItemProps,
} from "@/components/sidebar-menu";

// Dialog and Feedback Components
export {
  default as ConfirmDialog,
  createDialog,
  InfoDialog,
  WarningDialog,
  ErrorDialog,
  SuccessDialog,
  DeleteDialog,
} from "@/components/confirm-dialog";
export type {
  ConfirmDialogProps,
  ConfirmDialogType,
} from "@/components/confirm-dialog";

export {
  default as EmptyState,
  SearchEmptyState,
  DataEmptyState,
  ErrorEmptyState,
  LoadingEmptyState,
} from "@/components/empty-state";
export type { EmptyStateProps, EmptyStateType } from "@/components/empty-state";

// Custom Components
export { default as AppForm } from "@/components/form";
export type { FieldConfig } from "@/components/form";
export { default as Dialog } from "@/components/custom-dialog";
export { CustomSheet } from "@/components/sheet";
export { ScrollArea } from "@/components/ui/scroll-area";
export {
  default as DataTable,
  type SimpleColumnDef,
  type ActionButton,
  type SelectionOptions,
  type ActionsOptions,
} from "@/components/table";
export * from "@/components/card";
export { CustomDrawer } from "@/components/drawers";

// Shadcn UI Components
export * from "@/components/ui/badge";
export { Toaster } from "@/components/ui/sonner";
export { toast } from "sonner";
export * from "@/components/ui/checkbox";
export * from "@/components/ui/dropdown-menu";
export * from "@/components/ui/input";
export * from "@/components/ui/label";
export * from "@/components/ui/tabs";
export * from "@/components/ui/table";
export * from "@/components/ui/select";
export * from "@/components/ui/separator";
export * from "@/components/ui/switch";
export * from "@/components/ui/alert";
export * from "@/components/ui/accordion";
export * from "@/components/ui/progress";
export * from "@/components/ui/textarea";
export * from "@/components/ui/avatar";
export * from "@/components/ui/tooltip";
export * from "@/components/ui/button";
export * from "@/components/ui/collapsible";
export { DialogFooter } from "@/components/ui/dialog";
