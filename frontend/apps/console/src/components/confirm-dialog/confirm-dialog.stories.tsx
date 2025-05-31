// src/confirm-dialog/confirm-dialog.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import ConfirmDialog, { 
  InfoDialog, 
  WarningDialog, 
  ErrorDialog, 
  SuccessDialog, 
  DeleteDialog
} from './index';
import { Button } from '../ui/button';

const meta: Meta<typeof ConfirmDialog> = {
  title: 'UI/ConfirmDialog',
  component: ConfirmDialog,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ConfirmDialog>;

// Template for interactive dialogs
const DialogTemplate = (args: any) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        Open Dialog
      </Button>
      <ConfirmDialog 
        {...args} 
        isOpen={isOpen} 
        onConfirm={() => setIsOpen(false)} 
        onCancel={() => setIsOpen(false)} 
      />
    </>
  );
};

// Default Confirm Dialog
export const Default: Story = {
  render: (args) => <DialogTemplate {...args} />,
  args: {
    title: 'Confirm Action',
    message: 'Are you sure you want to perform this action?',
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel',
    type: 'confirm',
  },
};

// Info Dialog
export const Info: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Show Info</Button>
        <InfoDialog 
          isOpen={isOpen} 
          title={args.title}
          message={args.message}
          onConfirm={() => setIsOpen(false)} 
          onCancel={() => setIsOpen(false)} 
        />
      </>
    );
  },
  args: {
    title: 'Information',
    message: 'This operation has completed successfully.',
  },
};

// Warning Dialog
export const Warning: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Show Warning</Button>
        <WarningDialog 
          isOpen={isOpen} 
          title={args.title}
          message={args.message}
          onConfirm={() => setIsOpen(false)} 
          onCancel={() => setIsOpen(false)} 
        />
      </>
    );
  },
  args: {
    title: 'Warning',
    message: 'This action may have unintended consequences. Are you sure you want to proceed?',
  },
};

// Error Dialog
export const Error: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Show Error</Button>
        <ErrorDialog 
          isOpen={isOpen} 
          title={args.title}
          message={args.message}
          onConfirm={() => setIsOpen(false)} 
          onCancel={() => setIsOpen(false)} 
        />
      </>
    );
  },
  args: {
    title: 'Error',
    message: 'An error occurred while processing your request. Please try again later.',
  },
};

// Success Dialog
export const Success: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Show Success</Button>
        <SuccessDialog 
          isOpen={isOpen} 
          title={args.title}
          message={args.message}
          onConfirm={() => setIsOpen(false)} 
          onCancel={() => setIsOpen(false)} 
        />
      </>
    );
  },
  args: {
    title: 'Success',
    message: 'Your changes have been saved successfully!',
  },
};

// Delete Dialog
export const Delete: Story = {
  render: (args) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button variant="destructive" onClick={() => setIsOpen(true)}>Delete Item</Button>
        <DeleteDialog 
          isOpen={isOpen} 
          title={args.title}
          message={args.message}
          onConfirm={() => setIsOpen(false)} 
          onCancel={() => setIsOpen(false)} 
        />
      </>
    );
  },
  args: {
    title: 'Confirm Deletion',
    message: 'Are you sure you want to delete this item? This action cannot be undone.',
  },
};

// Loading Dialog
export const Loading: Story = {
  render: (args) => <DialogTemplate {...args} />,
  args: {
    title: 'Processing',
    message: 'Please wait while we process your request...',
    confirmLabel: 'OK',
    cancelLabel: 'Cancel',
    isLoading: true,
    type: 'info',
  },
};

// Dialog with custom content
export const WithCustomContent: Story = {
  render: (args) => <DialogTemplate {...args} />,
  args: {
    title: 'Custom Dialog',
    message: (
      <div>
        <p>This dialog contains <strong>custom content</strong>.</p>
        <ul className="list-disc pl-5 mt-2">
          <li>Item 1</li>
          <li>Item 2</li>
          <li>Item 3</li>
        </ul>
      </div>
    ),
    confirmLabel: 'Proceed',
    cancelLabel: 'Go Back',
    type: 'confirm',
  },
};

// Dialog with reversed buttons
export const ReversedButtons: Story = {
  render: (args) => <DialogTemplate {...args} />,
  args: {
    title: 'Confirm Action',
    message: 'Do you want to continue with this action?',
    confirmLabel: 'Yes, Continue',
    cancelLabel: 'No, Go Back',
    reverseButtons: true,
    type: 'warning',
  },
};
