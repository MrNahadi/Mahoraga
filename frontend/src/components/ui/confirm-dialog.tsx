import { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';

interface ConfirmDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'default' | 'destructive';
    isLoading?: boolean;
}

export function ConfirmDialog({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    variant = 'default',
    isLoading = false,
}: ConfirmDialogProps) {
    const dialogRef = useRef<HTMLDivElement>(null);
    const confirmButtonRef = useRef<HTMLButtonElement>(null);
    const previousActiveElement = useRef<HTMLElement | null>(null);

    // Store the previously focused element and focus the dialog
    useEffect(() => {
        if (isOpen) {
            previousActiveElement.current = document.activeElement as HTMLElement;
            // Focus the confirm button after a short delay
            setTimeout(() => {
                confirmButtonRef.current?.focus();
            }, 50);
        } else if (previousActiveElement.current) {
            previousActiveElement.current.focus();
        }
    }, [isOpen]);

    // Handle keyboard events
    const handleKeyDown = useCallback((event: KeyboardEvent) => {
        if (!isOpen) return;

        if (event.key === 'Escape') {
            event.preventDefault();
            onClose();
        }

        // Trap focus within dialog
        if (event.key === 'Tab' && dialogRef.current) {
            const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
                'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey && document.activeElement === firstElement) {
                event.preventDefault();
                lastElement?.focus();
            } else if (!event.shiftKey && document.activeElement === lastElement) {
                event.preventDefault();
                firstElement?.focus();
            }
        }
    }, [isOpen, onClose]);

    useEffect(() => {
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    // Prevent body scroll when dialog is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    return createPortal(
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dialog-title"
            aria-describedby="dialog-description"
        >
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
                aria-hidden="true"
            />

            {/* Dialog */}
            <div
                ref={dialogRef}
                className={cn(
                    "relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6",
                    "transform transition-all duration-200",
                    "focus:outline-none"
                )}
            >
                {/* Close button */}
                <button
                    onClick={onClose}
                    className={cn(
                        "absolute top-4 right-4 p-1 rounded-full text-gray-400",
                        "hover:bg-gray-100 hover:text-gray-600",
                        "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                        "transition-colors"
                    )}
                    aria-label="Close dialog"
                >
                    <X className="w-5 h-5" />
                </button>

                {/* Title */}
                <h2
                    id="dialog-title"
                    className="text-xl font-semibold text-gray-900 pr-8"
                >
                    {title}
                </h2>

                {/* Message */}
                <p
                    id="dialog-description"
                    className="mt-3 text-gray-600"
                >
                    {message}
                </p>

                {/* Actions */}
                <div className="mt-6 flex justify-end space-x-3">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        disabled={isLoading}
                        className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    >
                        {cancelLabel}
                    </Button>
                    <Button
                        ref={confirmButtonRef}
                        variant={variant === 'destructive' ? 'destructive' : 'default'}
                        onClick={onConfirm}
                        disabled={isLoading}
                        className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    >
                        {isLoading ? (
                            <span className="flex items-center space-x-2">
                                <svg
                                    className="animate-spin h-4 w-4"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    />
                                </svg>
                                <span>Loading...</span>
                            </span>
                        ) : (
                            confirmLabel
                        )}
                    </Button>
                </div>
            </div>
        </div>,
        document.body
    );
}
