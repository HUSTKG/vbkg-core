import { PaginatedResponse } from "@vbkg/types";

// packages/utils/src/index.ts
export * from "./formatting/date";
export * from "./constants";
export * from './helpers';

// Common Functions
export function isValidJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return function (...args: Parameters<T>) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Type Guards
export function isApiError(
  error: unknown,
): error is Error & { response?: { status: number } } {
  return error instanceof Error && "response" in error;
}

export function isPaginatedResponse<T>(
  response: unknown,
): response is PaginatedResponse<T> {
  return (
    typeof response === "object" &&
    response !== null &&
    "data" in response &&
    "meta" in response &&
    Array.isArray((response as PaginatedResponse<T>).data)
  );
}
