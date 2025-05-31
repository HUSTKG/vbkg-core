import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { XIcon } from "lucide-react";
import { ReactNode } from "react";

// Define types for the sheet props
type SheetSide = "top" | "right" | "bottom" | "left";
type SheetSize = "sm" | "default" | "lg" | "xl" | "full";

// Interface for our reusable sheet component props
interface ReusableSheetProps {
  /** The content that will trigger the sheet to open */
  trigger?: ReactNode;
  /** The title of the sheet */
  title?: string;
  /** Optional description text */
  description?: string;
  /** The main content of the sheet */
  children: ReactNode;
  /** Footer content (usually actions like buttons) */
  footer?: ReactNode;
  /** Side from which the sheet appears: 'left', 'right', 'top', 'bottom' */
  side?: SheetSide;
  /** Size of the sheet, affects width or height depending on side */
  size?: SheetSize;
  /** Whether the sheet can be closed by clicking outside or pressing escape */
  modal?: boolean;
  /** Custom classes for the sheet content */
  className?: string;
  /** Optional class name for the trigger button */
  open?: boolean;
  /** Optional function to handle opening the sheet */
  buttonText?: string;
  /** Optional function to handle opening the sheet */
  onOpenChange?: (open: boolean) => void;
}

// Props for our reusable sheet component
export const CustomSheet = ({
  trigger,
  title,
  open,
  onOpenChange,
  description,
  children,
  footer,
  side = "right",
  size = "default",
  modal = true,
  buttonText,
  className = "",
}: ReusableSheetProps) => {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} modal={modal}>
      <SheetTrigger asChild>
        {trigger ? (
          trigger
        ) : (
          <Button variant="outline" className="w-full">
            {buttonText || "Open Sheet"}
          </Button>
        )}
      </SheetTrigger>
      <SheetContent
        side={side}
        className={cn(
          "overflow-y-auto",
          size === "sm" && "sm:max-w-[300px] md:max-w-[400px] lg:max-w-[500px]",
          size === "default" &&
            "sm:max-w-[400px] md:max-w-[500px] lg:max-w-[600px]",
          size === "lg" && "sm:max-w-[500px] md:max-w-[600px] lg:max-w-[700px]",
          size === "xl" && "sm:max-w-[600px] md:max-w-[700px] lg:max-w-[800px]",
          size === "full" && "sm:max-w-full",
          className,
        )}
      >
        <SheetHeader className="flex items-start flex-row justify-between sticky top-0 bg-white/80">
          <div>
            {title && <SheetTitle>{title}</SheetTitle>}
            {description && <SheetDescription>{description}</SheetDescription>}
          </div>
          <div
            onClick={() => onOpenChange && onOpenChange(false)}
            className="ring-offset-background focus:ring-ring data-[state=open]:bg-secondary rounded-xs opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none"
          >
            <XIcon className="size-4" />
            <span className="sr-only">Close</span>
          </div>
        </SheetHeader>

        <div>{children}</div>

        {footer && (
          <SheetFooter className="flex justify-end gap-2">{footer}</SheetFooter>
        )}
      </SheetContent>
    </Sheet>
  );
};
