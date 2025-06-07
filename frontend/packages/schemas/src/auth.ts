import { z } from "zod";

export const loginSchema = z.object({
email: z.string().email("Địa chỉ email không hợp lệ"),
  password: z
    .string()
    .min(8, "Mật khẩu phải có ít nhất 8 ký tự")
    .regex(
      /(?=.*[0-9])(?=.*[A-Z])/,
    "Mật khẩu phải chứa ít nhất một chữ hoa và một chữ số",
    ),
});

export const registerSchema = loginSchema
  .extend({
    fullname: z.string().optional(),
    confirmPassword: z
      .string()
    .min(8, "Mật khẩu xác nhận phải có ít nhất 8 ký tự")
      .regex(
        /(?=.*[0-9])(?=.*[A-Z])/,
        "Mật khẩu xác nhận phải chứa ít nhất một chữ hoa và một chữ số",
      ),
    roles: z.array(z.string()).optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Mật khẩu xác nhận không khớp",
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
