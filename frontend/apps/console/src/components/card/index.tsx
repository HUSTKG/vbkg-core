import React from "react";
import { cn } from "@/lib/utils";
import {
  Card as ShadcnCard,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// Types for our composable card component
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export interface CardTitleProps
  extends React.HTMLAttributes<HTMLHeadingElement> {
  className?: string;
}

export interface CardDescriptionProps
  extends React.HTMLAttributes<HTMLParagraphElement> {
  className?: string;
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

// Main card component
const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <ShadcnCard
      ref={ref}
      className={cn("overflow-hidden", className)}
      {...props}
    />
  ),
);
Card.displayName = "Card";

// Card header component
const Header = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <CardHeader ref={ref} className={cn("", className)} {...props} />
  ),
);
Header.displayName = "Card.Header";

// Card title component
const Title = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, ...props }, ref) => (
    <CardTitle
      ref={ref}
      className={cn("text-xl font-semibold", className)}
      {...props}
    />
  ),
);
Title.displayName = "Card.Title";

// Card description component
const Description = React.forwardRef<
  HTMLParagraphElement,
  CardDescriptionProps
>(({ className, ...props }, ref) => (
  <CardDescription
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
Description.displayName = "Card.Description";

// Card content component
const Content = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <CardContent ref={ref} className={cn("", className)} {...props} />
  ),
);
Content.displayName = "Card.Content";

// Card footer component
const Footer = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <CardFooter
      ref={ref}
      className={cn("flex items-center p-6 pt-0", className)}
      {...props}
    />
  ),
);
Footer.displayName = "Card.Footer";

// Compose the components
export {
  Card,
  Header as CardHeader,
  Title as CardTitle,
  Description as CardDescription,
  Content as CardContent,
  Footer as CardFooter,
};
