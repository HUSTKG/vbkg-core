import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters long")
    .regex(
      /(?=.*[0-9])(?=.*[A-Z])/,
      "Password must contain at least one uppercase letter and one digit",
    ),
});

export const registerSchema = loginSchema
  .extend({
    fullname: z.string().optional(),
    confirmPassword: z
      .string()
      .min(8, "Password must be at least 8 characters long")
      .regex(
        /(?=.*[0-9])(?=.*[A-Z])/,
        "Password must contain at least one uppercase letter and one digit",
      ),
    roles: z.array(z.string()).optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

// Schema for JSON-based login
export const LoginJsonSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

// Schema for logout
export const LogoutSchema = z.object({
  token: z.string().min(1), // Token is required
});
