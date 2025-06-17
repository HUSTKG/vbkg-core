import { z } from "zod";

const literalSchema = z.union([z.string(), z.number(), z.boolean(), z.null()]);
type Literal = z.infer<typeof literalSchema>;
type Json = Literal | { [key: string]: Json } | Json[];
export const jsonSchema: z.ZodType<Json> = z.lazy(() =>
	z.union([literalSchema, z.array(jsonSchema), z.record(jsonSchema)]),
);

const json = () => jsonSchema;

export const stringToJSONSchema = z
	.string()
	.transform((str, ctx): z.infer<ReturnType<typeof json>> => {
		try {
			return JSON.parse(str);
		} catch (e) {
			ctx.addIssue({ code: "custom", message: "Invalid JSON" });
			return z.NEVER;
		}
	});

// Schema để validate Cypher query string
export const CypherQuerySchema = z
	.string()
	.trim()
	.optional()
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra query phải bắt đầu bằng các keyword hợp lệ
		const validStarters = [
			"MATCH",
			"CREATE",
			"MERGE",
			"DELETE",
			"SET",
			"REMOVE",
			"RETURN",
			"WITH",
			"UNWIND",
			"CALL",
			"OPTIONAL MATCH",
		];

		const upperQuery = query.toUpperCase();
		return validStarters.some((starter) => upperQuery.startsWith(starter));
	}, "Cypher query phải bắt đầu với keyword hợp lệ (MATCH, CREATE, MERGE, etc.)")
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra cân bằng dấu ngoặc
		const parentheses =
			(query.match(/\(/g) || []).length - (query.match(/\)/g) || []).length;
		return parentheses === 0;
	}, "Dấu ngoặc tròn () không cân bằng")
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra cân bằng dấu ngoặc vuông
		const brackets =
			(query.match(/\[/g) || []).length - (query.match(/\]/g) || []).length;
		return brackets === 0;
	}, "Dấu ngoặc vuông [] không cân bằng")
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra cân bằng dấu ngoặc nhọn
		const braces =
			(query.match(/\{/g) || []).length - (query.match(/\}/g) || []).length;
		return braces === 0;
	}, "Dấu ngoặc nhọn {} không cân bằng")
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra cân bằng dấu nháy đôi
		const quotes = (query.match(/"/g) || []).length;
		return quotes % 2 === 0;
	}, 'Dấu nháy đôi " không cân bằng')
	.refine((query) => {
		if (!query) return true; // Nếu không có query, không cần kiểm tra
		// Kiểm tra cân bằng dấu nháy đơn
		const singleQuotes = (query.match(/'/g) || []).length;
		return singleQuotes % 2 === 0;
	}, "Dấu nháy đơn ' không cân bằng");

// Main Cypher query schema
