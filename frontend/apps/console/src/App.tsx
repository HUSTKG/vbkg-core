import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { initializeApi } from "@vbkg/api-client";
import { RouterProvider } from "react-router";
import { router } from "./router";
import { getSession } from "@vbkg/utils";

export const queryClient = new QueryClient();

initializeApi({
  baseUrl: import.meta.env.VITE_API_URL! + import.meta.env.VITE_API_VERSION!,
  bearerToken: getSession()?.session.accessToken,
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
