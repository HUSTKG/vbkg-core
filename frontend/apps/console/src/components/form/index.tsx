import { useEffect, useState, useCallback, useRef } from "react";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
	Form,
	FormControl,
	FormDescription,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Calendar } from "@/components/ui/calendar";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/popover";
import { format } from "date-fns";
import {
	CalendarIcon,
	Plus,
	Trash2,
	ChevronUp,
	ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
	Card,
	CardContent,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/accordion";

// Type definitions for form field options
type SelectOption = {
	label: string;
	value: string;
};

type RadioOption = {
	label: string;
	value: string;
};

type CheckboxOption = {
	label: string;
	value: string;
};

// Extended field type definition
export type FieldConfig = {
	name: string;
	label: string;
	colSpan?: number;
	type:
		| "text"
		| "email"
		| "password"
		| "number"
		| "textarea"
		| "select"
		| "checkbox"
		| "radio"
		| "switch"
		| "date"
		| "hidden"
		| "object"
		| "array"
		| "color"
		| "custom";
	placeholder?: string;
	description?: string;
	defaultValue?: any;
	required?: boolean;
	disabled?: boolean;
	options?: SelectOption[] | RadioOption[] | CheckboxOption[];
	validation?: z.ZodTypeAny;
	className?: string;
	// For object and array fields
	fields?: FieldConfig[];
	arrayItemLabel?: string;
	wrapperClassName?: string;
	minItems?: number;
	maxItems?: number;
	collapsible?: boolean;
	customComponent?: React.FC<{
		name: string;
		label?: string;
		placeholder?: string;
		value: any;
		onChange: (value: any) => void;
	}>;
};

// Form props
export interface GeneralFormProps<T extends z.ZodType> {
	fields: FieldConfig[] | ((data: z.infer<T>) => FieldConfig[]);
	schema: T;
	onSubmit: (data: z.infer<T>) => void;
	onError?: (errors: any) => void;
	submitButtonText?: string;
	debug?: boolean;
	resetButtonText?: string;
	resetButton?: boolean;
	defaultValues?: Partial<z.infer<T>>;
	buttons?: React.ReactNode;
	className?: string;
	isLoading?: boolean;
	watchFields?: string[];
}

const GeneralForm = <T extends z.ZodType>({
	fields,
	schema,
	onSubmit,
	onError,
	submitButtonText = "Submit",
	debug,
	resetButtonText = "Reset",
	buttons,
	resetButton = false,
	defaultValues = {},
	className = "",
	isLoading = false,
	watchFields = [],
}: GeneralFormProps<T>) => {
	const [submitSuccess, setSubmitSuccess] = useState(false);

	// Store the fields function reference
	const fieldsRef = useRef(fields);
	useEffect(() => {
		fieldsRef.current = fields;
	}, [fields]);

	// Get initial fields config
	const initialFields =
		typeof fieldsRef.current === "function"
			? fieldsRef.current({})
			: fieldsRef.current;

	// State for dynamic fields
	const [currentFields, setCurrentFields] =
		useState<FieldConfig[]>(initialFields);

	// Flag to prevent infinite updates
	const isUpdatingFields = useRef(false);

	// Prepare default values for the form
	const formDefaultValues = initialFields.reduce(
		(acc, field) => {
			if (defaultValues[field.name] !== undefined) {
				acc[field.name] = defaultValues[field.name];
			} else {
				acc[field.name] = getFieldDefaultValue(field);
			}
			return acc;
		},
		{} as Record<string, any>,
	);

	const renderNestedField = (
		field: FieldConfig,
		path: string,
		disabled: boolean = false,
	) => {
		const fieldPath = path ? `${path}.${field.name}` : field.name;

		switch (field.type) {
			case "text":
			case "email":
			case "password":
			case "color":
			case "number":
			case "hidden":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem key={fieldPath} className={field.className}>
								{field.type !== "hidden" && (
									<FormLabel>
										{field.label}
										{field.required && <span className="text-red-500">*</span>}
									</FormLabel>
								)}
								<FormControl>
									<Input
										{...formField}
										type={field.type}
										placeholder={field.placeholder}
										disabled={field.disabled || disabled || isLoading}
										className={field.type === "hidden" ? "hidden" : ""}
									/>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "textarea":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem key={fieldPath} className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									<Textarea
										{...formField}
										placeholder={field.placeholder}
										disabled={field.disabled || disabled || isLoading}
									/>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "select":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<Select
									onValueChange={formField.onChange}
									value={formField.value || ""}
									disabled={field.disabled || disabled || isLoading}
								>
									<FormControl>
										<SelectTrigger>
											<SelectValue placeholder={field.placeholder} />
										</SelectTrigger>
									</FormControl>
									<SelectContent>
										{field.options?.map((option) => (
											<SelectItem key={option.value} value={option.value}>
												{option.label}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "checkbox":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								{field.options?.map((option) => (
									<div
										key={option.value}
										className="flex items-center space-x-2"
									>
										<FormControl>
											<Checkbox
												checked={formField.value?.includes(option.value)}
												onCheckedChange={(checked) => {
													let updatedValue = [...(formField.value || [])];
													if (checked) {
														updatedValue.push(option.value);
													} else {
														updatedValue = updatedValue.filter(
															(val) => val !== option.value,
														);
													}
													formField.onChange(updatedValue);
												}}
												disabled={field.disabled || disabled || isLoading}
											/>
										</FormControl>
										<label className="text-sm font-medium leading-none cursor-pointer">
											{option.label}
										</label>
									</div>
								))}
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "radio":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									<RadioGroup
										onValueChange={formField.onChange}
										value={formField.value}
										className="flex flex-col space-y-1"
										disabled={field.disabled || disabled || isLoading}
									>
										{field.options?.map((option) => (
											<div
												key={option.value}
												className="flex items-center space-x-2"
											>
												<RadioGroupItem
													value={option.value}
													id={`${fieldPath}-${option.value}`}
												/>
												<label
													htmlFor={`${fieldPath}-${option.value}`}
													className="text-sm font-medium leading-none cursor-pointer"
												>
													{option.label}
												</label>
											</div>
										))}
									</RadioGroup>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "switch":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem
								className={cn(
									"flex flex-row items-center justify-between rounded-lg border px-4 py-2",
									field.className,
								)}
							>
								<div className="space-y-0.5 w-full">
									<FormLabel className="flex items-center justify-between">
										<div className="flex items-center space-x-2">
											{field.label}
											{field.required && (
												<span className="text-red-500">*</span>
											)}
										</div>
										<FormControl>
											<Switch
												checked={formField.value}
												onCheckedChange={formField.onChange}
												disabled={field.disabled || disabled || isLoading}
											/>
										</FormControl>
									</FormLabel>
									{field.description && (
										<FormDescription>{field.description}</FormDescription>
									)}
								</div>
							</FormItem>
						)}
					/>
				);

			case "date":
				return (
					<FormField
						name={fieldPath}
						control={form.control}
						key={fieldPath}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<Popover>
									<PopoverTrigger asChild>
										<FormControl>
											<Button
												variant={"outline"}
												className={cn(
													"w-full pl-3 text-left font-normal",
													!formField.value && "text-muted-foreground",
												)}
												disabled={field.disabled || disabled || isLoading}
											>
												{formField.value ? (
													format(formField.value, "PPP")
												) : (
													<span>{field.placeholder || "Select a date"}</span>
												)}
												<CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
											</Button>
										</FormControl>
									</PopoverTrigger>
									<PopoverContent className="w-auto p-0" align="start">
										<Calendar
											mode="single"
											selected={formField.value}
											onSelect={formField.onChange}
											disabled={field.disabled || disabled || isLoading}
										/>
									</PopoverContent>
								</Popover>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "object":
				return renderNestedObjectField(field, fieldPath, disabled);

			case "array":
				return renderNestedArrayField(field, fieldPath, disabled);

			case "custom":
				return (
					<Controller
						key={fieldPath}
						name={fieldPath}
						control={form.control}
						render={({ field: formField }) => (
							<FormItem key={fieldPath} className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									{field.customComponent ? (
										<field.customComponent
											name={fieldPath}
											label={field.label}
											placeholder={field.placeholder}
											value={formField.value}
											onChange={formField.onChange}
										/>
									) : null}
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			default:
				return null;
		}
	};

	// Initialize form
	const form = useForm({
		resolver: zodResolver(schema),
		defaultValues: formDefaultValues,
		mode: "onBlur",
	});

	if (debug) {
		console.log("Current Fields: ", currentFields);
		console.log("Initial Fields: ", initialFields);
		console.log("Default Values: ", defaultValues);
		console.log("Form State: ", form.getValues());
		console.log("Form Errors: ", form.formState.errors);
		console.log("Form Watch: ", form.watch());
	}

	// Memoize fields generation function to prevent constant rerenders
	const generateFields = useCallback((data: any) => {
		if (typeof fieldsRef.current === "function") {
			return fieldsRef.current(data);
		}
		return fieldsRef.current as FieldConfig[];
	}, []);

	// Use a custom hook with manual implementation of watching fields
	useEffect(() => {
		// Only register for specific fields if watchFields is provided
		if (watchFields.length === 0 && typeof fieldsRef.current !== "function") {
			return; // No need to watch if we don't have dynamic fields
		}

		// Update fields function to avoid the React Hook Form watch() which can cause loops
		const subscription = form.watch((value, { name }) => {
			// Only update fields if we're watching this specific field or if we're watching all fields
			if (
				!isUpdatingFields.current &&
				(watchFields.length === 0 || watchFields.includes(name as string))
			) {
				// Prevent re-entry
				isUpdatingFields.current = true;

				// Generate new fields with the current form data
				try {
					const newFields = generateFields(value);
					// Only update if fields have actually changed
					if (JSON.stringify(newFields) !== JSON.stringify(currentFields)) {
						setCurrentFields(newFields);
					}
				} finally {
					// Reset flag after a short delay to ensure React has processed the update
					setTimeout(() => {
						isUpdatingFields.current = false;
					}, 0);
				}
			}
		});

		// Clean up subscription
		return () => subscription.unsubscribe();
	}, [form, generateFields, watchFields, currentFields]);

	// Handle form submission
	const handleSubmit = async (data: z.infer<T>) => {
		try {
			onSubmit(data);
			setSubmitSuccess(true);
			if (!resetButton) {
				form.reset(formDefaultValues);
			}
			// Hide success message after 3 seconds
			setTimeout(() => setSubmitSuccess(false), 3000);
		} catch (error) {
			console.error("Form submission error:", error);
		}
	};

	// Handle form errors
	const handleError = (errors: any) => {
		console.error("Form validation errors:", errors);
		if (onError) onError(errors);
	};

	// Render object field type
	const renderObjectField = (field: FieldConfig) => {
		if (!field.fields || field.fields.length === 0) {
			return null;
		}

		return (
			<FormField
				key={field.name}
				control={form.control}
				name={field.name}
				render={() => (
					<FormItem className={cn("space-y-3", field.className)}>
						<FormLabel>
							{field.label}
							{field.required && <span className="text-red-500">*</span>}
						</FormLabel>
						{field.description && (
							<FormDescription>{field.description}</FormDescription>
						)}

						<Card>
							<CardContent className="space-y-4">
								{field.fields?.map((nestedField) => (
									<div key={nestedField.name}>
										{renderNestedField(nestedField, field.name, field.disabled)}
									</div>
								))}
							</CardContent>
						</Card>
						<FormMessage />
					</FormItem>
				)}
			/>
		);
	};

	// Render array field type
	const renderArrayField = (field: FieldConfig) => {
		if (!field.fields || field.fields.length === 0) {
			return null;
		}

		return (
			<FormField
				key={field.name}
				control={form.control}
				name={field.name}
				render={() => {
					const fieldArray = useFieldArray({
						name: field.name,
						control: form.control,
					});

					return (
						<FormItem className={cn("space-y-3", field.className)}>
							<div className="flex items-center justify-between">
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								{!field.disabled && !isLoading && (
									<Button
										type="button"
										variant="outline"
										size="sm"
										onClick={() => {
											const newItem = field.fields?.reduce(
												(acc: Record<string, any>, itemField) => {
													acc[itemField.name] = getFieldDefaultValue(itemField);
													return acc;
												},
												{},
											);

											// Check if max items is defined and respected
											if (
												field.maxItems === undefined ||
												fieldArray.fields.length < field.maxItems
											) {
												fieldArray.append(newItem);
											}
										}}
										disabled={
											(field.maxItems !== undefined &&
												fieldArray.fields.length >= field.maxItems) ||
											field.disabled ||
											isLoading
										}
									>
										<Plus className="h-4 w-4 mr-2" />
										Thêm {field.arrayItemLabel || "Item"}
									</Button>
								)}
							</div>

							{field.description && (
								<FormDescription>{field.description}</FormDescription>
							)}

							<div className="space-y-4">
								{fieldArray.fields.length === 0 ? (
									<p className="text-sm text-muted-foreground text-center py-4 border rounded-md">
										No items added. Click the button above to add an item.
									</p>
								) : (
									fieldArray.fields.map((item, index) => (
										<Card key={item.id} className="p-0 gap-0">
											{field.collapsible ? (
												<Accordion type="single" collapsible className="w-full">
													<AccordionItem
														value={`item-${index}`}
														className="border-none"
													>
														<CardHeader className="p-0 gap-0">
															<AccordionTrigger className="p-3 rounded-0 rounded-t-5 hover:bg-gray-100 hover:no-underline cursor-pointer">
																<div className="flex-1 text-left">
																	{field.arrayItemLabel || "Item"} #{index + 1}
																</div>
															</AccordionTrigger>
														</CardHeader>
														<AccordionContent className="pb-0">
															<CardContent className="p-3 gap-4">
																{field.fields?.map((nestedField) => (
																	<div
																		key={nestedField.name}
																		className={nestedField.wrapperClassName}
																	>
																		{renderNestedField(
																			nestedField,
																			`${field.name}.${index}`,
																			field.disabled,
																		)}
																	</div>
																))}
															</CardContent>
														</AccordionContent>
													</AccordionItem>
												</Accordion>
											) : (
												<>
													<CardHeader className="p-3! py-2">
														<CardTitle className="text-base flex items-center justify-between">
															<span>
																{field.arrayItemLabel || "Item"} #{index + 1}
															</span>
														</CardTitle>
													</CardHeader>
													<CardContent className="p-3 pt-0 gap-4">
														{field.fields?.map((nestedField) => (
															<div
																key={nestedField.name}
																className={nestedField.wrapperClassName}
															>
																{renderNestedField(
																	nestedField,
																	`${field.name}.${index}`,
																	field.disabled,
																)}
															</div>
														))}
													</CardContent>
												</>
											)}

											<CardFooter className="flex justify-between border-t p-3!">
												<div className="flex space-x-2">
													{index > 0 && !field.disabled && !isLoading && (
														<Button
															type="button"
															variant="outline"
															size="sm"
															onClick={() => fieldArray.swap(index, index - 1)}
														>
															<ChevronUp className="h-4 w-4" />
														</Button>
													)}
													{index < fieldArray.fields.length - 1 &&
														!field.disabled &&
														!isLoading && (
															<Button
																type="button"
																variant="outline"
																size="sm"
																onClick={() =>
																	fieldArray.swap(index, index + 1)
																}
															>
																<ChevronDown className="h-4 w-4" />
															</Button>
														)}
												</div>

												{!field.disabled && !isLoading && (
													<Button
														type="button"
														variant="destructive"
														size="sm"
														onClick={() => {
															// Check if min items is defined and respected
															if (
																field.minItems === undefined ||
																fieldArray.fields.length > field.minItems
															) {
																fieldArray.remove(index);
															}
														}}
														disabled={
															(field.minItems !== undefined &&
																fieldArray.fields.length <= field.minItems) ||
															field.disabled ||
															isLoading
														}
													>
														<Trash2 className="h-4 w-4 mr-2" />
														Xóa {field.arrayItemLabel || "Item"}
													</Button>
												)}
											</CardFooter>
										</Card>
									))
								)}
							</div>
							<FormMessage />
						</FormItem>
					);
				}}
			/>
		);
	};

	const renderNestedObjectField = (
		field: FieldConfig,
		fieldPath: string,
		disabled: boolean = false,
	) => {
		if (!field.fields || field.fields.length === 0) {
			return null;
		}

		return (
			<FormField
				key={fieldPath}
				control={form.control}
				name={fieldPath}
				render={() => (
					<FormItem className={cn("space-y-3", field.className)}>
						<FormLabel>
							{field.label}
							{field.required && <span className="text-red-500">*</span>}
						</FormLabel>
						{field.description && (
							<FormDescription>{field.description}</FormDescription>
						)}

						<Card>
							<CardContent className="space-y-4 pt-6">
								{field.fields?.map((nestedField) => (
									<div key={nestedField.name}>
										{renderNestedField(
											nestedField,
											fieldPath,
											field.disabled || disabled,
										)}
									</div>
								))}
							</CardContent>
						</Card>
						<FormMessage />
					</FormItem>
				)}
			/>
		);
	};

	const renderNestedArrayField = (
		field: FieldConfig,
		fieldPath: string,
		disabled: boolean = false,
	) => {
		if (!field.fields || field.fields.length === 0) {
			return null;
		}

		return (
			<FormField
				key={fieldPath}
				control={form.control}
				name={fieldPath}
				render={() => {
					const fieldArray = useFieldArray({
						name: fieldPath,
						control: form.control,
					});

					return (
						<FormItem className={cn("space-y-3", field.className)}>
							<div className="flex items-center justify-between">
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								{!field.disabled && !disabled && !isLoading && (
									<Button
										type="button"
										variant="outline"
										size="sm"
										onClick={() => {
											const newItem = field.fields?.reduce(
												(acc: Record<string, any>, itemField) => {
													acc[itemField.name] = getFieldDefaultValue(itemField);
													return acc;
												},
												{},
											);

											// Check if max items is defined and respected
											if (
												field.maxItems === undefined ||
												fieldArray.fields.length < field.maxItems
											) {
												fieldArray.append(newItem);
											}
										}}
										disabled={
											(field.maxItems !== undefined &&
												fieldArray.fields.length >= field.maxItems) ||
											field.disabled ||
											disabled ||
											isLoading
										}
									>
										<Plus className="h-4 w-4 mr-2" />
										Thêm {field.arrayItemLabel || "Item"}
									</Button>
								)}
							</div>

							{field.description && (
								<FormDescription>{field.description}</FormDescription>
							)}

							<div className="space-y-4">
								{fieldArray.fields.length === 0 ? (
									<p className="text-sm text-muted-foreground text-center py-4 border rounded-md">
										Chưa có mục nào. Nhấn nút trên để thêm mục.
									</p>
								) : (
									fieldArray.fields.map((item, index) => (
										<Card key={item.id} className="p-0 gap-0">
											{field.collapsible ? (
												<Accordion type="single" collapsible className="w-full">
													<AccordionItem
														value={`item-${index}`}
														className="border-none"
													>
														<CardHeader className="p-0 gap-0">
															<AccordionTrigger className="p-3 rounded-0 rounded-t-5 hover:bg-gray-100 hover:no-underline cursor-pointer">
																<div className="flex-1 text-left">
																	{field.arrayItemLabel || "Item"} #{index + 1}
																</div>
															</AccordionTrigger>
														</CardHeader>
														<AccordionContent className="pb-0">
															<CardContent className="p-3 gap-4">
																{field.fields?.map((nestedField) => (
																	<div
																		key={nestedField.name}
																		className={nestedField.wrapperClassName}
																	>
																		{renderNestedField(
																			nestedField,
																			`${fieldPath}.${index}`,
																			field.disabled || disabled,
																		)}
																	</div>
																))}
															</CardContent>
														</AccordionContent>
													</AccordionItem>
												</Accordion>
											) : (
												<>
													<CardHeader className="p-3! py-2">
														<CardTitle className="text-base flex items-center justify-between">
															<span>
																{field.arrayItemLabel || "Item"} #{index + 1}
															</span>
														</CardTitle>
													</CardHeader>
													<CardContent className="p-3 pt-0 space-y-4 gap-4">
														{field.fields?.map((nestedField) => (
															<div
																key={nestedField.name}
																className={nestedField.wrapperClassName}
															>
																{renderNestedField(
																	nestedField,
																	`${fieldPath}.${index}`,
																	field.disabled || disabled,
																)}
															</div>
														))}
													</CardContent>
												</>
											)}

											<CardFooter className="flex justify-between border-t p-3!">
												<div className="flex space-x-2">
													{index > 0 &&
														!field.disabled &&
														!disabled &&
														!isLoading && (
															<Button
																type="button"
																variant="outline"
																size="sm"
																onClick={() =>
																	fieldArray.swap(index, index - 1)
																}
															>
																<ChevronUp className="h-4 w-4" />
															</Button>
														)}
													{index < fieldArray.fields.length - 1 &&
														!field.disabled &&
														!disabled &&
														!isLoading && (
															<Button
																type="button"
																variant="outline"
																size="sm"
																onClick={() =>
																	fieldArray.swap(index, index + 1)
																}
															>
																<ChevronDown className="h-4 w-4" />
															</Button>
														)}
												</div>

												{!field.disabled && !disabled && !isLoading && (
													<Button
														type="button"
														variant="destructive"
														size="sm"
														onClick={() => {
															// Check if min items is defined and respected
															if (
																field.minItems === undefined ||
																fieldArray.fields.length > field.minItems
															) {
																fieldArray.remove(index);
															}
														}}
														disabled={
															(field.minItems !== undefined &&
																fieldArray.fields.length <= field.minItems) ||
															field.disabled ||
															disabled ||
															isLoading
														}
													>
														<Trash2 className="h-4 w-4 mr-2" />
														Xóa {field.arrayItemLabel || "Item"}
													</Button>
												)}
											</CardFooter>
										</Card>
									))
								)}
							</div>
							<FormMessage />
						</FormItem>
					);
				}}
			/>
		);
	};

	// Render form field based on field type
	const renderField = (field: FieldConfig) => {
		switch (field.type) {
			case "text":
			case "email":
			case "password":
			case "number":
			case "hidden":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem
								className={cn(getColSpanClass(field.colSpan), field.className)}
							>
								{field.type !== "hidden" && (
									<FormLabel>
										{field.label}
										{field.required && <span className="text-red-500">*</span>}
									</FormLabel>
								)}
								<FormControl>
									<Input
										{...formField}
										type={field.type}
										placeholder={field.placeholder}
										disabled={field.disabled || isLoading}
										className={field.type === "hidden" ? "hidden" : ""}
									/>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "textarea":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem
								className={cn(getColSpanClass(field.colSpan), field.className)}
							>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									<Textarea
										{...formField}
										placeholder={field.placeholder}
										disabled={field.disabled || isLoading}
									/>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "select":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem
								className={cn(getColSpanClass(field.colSpan), field.className)}
							>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<Select
									onValueChange={formField.onChange}
									value={formField.value}
									disabled={field.disabled || isLoading}
								>
									<FormControl>
										<SelectTrigger>
											<SelectValue placeholder={field.placeholder} />
										</SelectTrigger>
									</FormControl>
									<SelectContent>
										{field.options?.map((option) => (
											<SelectItem key={option.value} value={option.value}>
												{option.label}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "checkbox":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem
								className={cn(getColSpanClass(field.colSpan), field.className)}
							>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								{field.options?.map((option) => (
									<div
										key={option.value}
										className="flex items-center space-x-2"
									>
										<FormControl>
											<Checkbox
												checked={formField.value?.includes(option.value)}
												onCheckedChange={(checked) => {
													let updatedValue = [...(formField.value || [])];
													if (checked) {
														updatedValue.push(option.value);
													} else {
														updatedValue = updatedValue.filter(
															(val) => val !== option.value,
														);
													}
													formField.onChange(updatedValue);
												}}
												disabled={field.disabled || isLoading}
											/>
										</FormControl>
										<label className="text-sm font-medium leading-none cursor-pointer">
											{option.label}
										</label>
									</div>
								))}
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "radio":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									<RadioGroup
										onValueChange={formField.onChange}
										value={formField.value}
										className="flex flex-col space-y-1"
										disabled={field.disabled || isLoading}
									>
										{field.options?.map((option) => (
											<div
												key={option.value}
												className="flex items-center space-x-2"
											>
												<RadioGroupItem
													value={option.value}
													id={`${field.name}-${option.value}`}
												/>
												<label
													htmlFor={`${field.name}-${option.value}`}
													className="text-sm font-medium leading-none cursor-pointer"
												>
													{option.label}
												</label>
											</div>
										))}
									</RadioGroup>
								</FormControl>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "switch":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem
								className={cn(
									"flex flex-row items-center justify-between rounded-lg border p-4",
									field.className,
								)}
							>
								<div className="space-y-0.5 w-full">
									<FormLabel className="flex items-center justify-between">
										<div>
											{field.label}
											{field.required && (
												<span className="text-red-500">*</span>
											)}
										</div>
										<FormControl>
											<Switch
												checked={formField.value}
												onCheckedChange={formField.onChange}
												disabled={field.disabled || isLoading}
											/>
										</FormControl>
									</FormLabel>
									{field.description && (
										<FormDescription>{field.description}</FormDescription>
									)}
								</div>
							</FormItem>
						)}
					/>
				);

			case "date":
				return (
					<FormField
						key={field.name}
						control={form.control}
						name={field.name}
						render={({ field: formField }) => (
							<FormItem className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<Popover>
									<PopoverTrigger asChild>
										<FormControl>
											<Button
												variant={"outline"}
												className={cn(
													"w-full pl-3 text-left font-normal",
													!formField.value && "text-muted-foreground",
												)}
												disabled={field.disabled || isLoading}
											>
												{formField.value ? (
													format(formField.value, "PPP")
												) : (
													<span>{field.placeholder || "Select a date"}</span>
												)}
												<CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
											</Button>
										</FormControl>
									</PopoverTrigger>
									<PopoverContent className="w-auto p-0" align="start">
										<Calendar
											mode="single"
											selected={formField.value}
											onSelect={formField.onChange}
											disabled={field.disabled || isLoading}
										/>
									</PopoverContent>
								</Popover>
								{field.description && (
									<FormDescription>{field.description}</FormDescription>
								)}
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			case "object":
				return renderObjectField(field);

			case "array":
				return renderArrayField(field);

			case "custom":
				return (
					<Controller
						key={field.name}
						name={field.name}
						control={form.control}
						render={({ field: formField }) => (
							<FormItem key={field.name} className={field.className}>
								<FormLabel>
									{field.label}
									{field.required && <span className="text-red-500">*</span>}
								</FormLabel>
								<FormControl>
									{field.customComponent ? (
										<field.customComponent
											name={field.name}
											label={field.label}
											placeholder={field.placeholder}
											value={formField.value}
											onChange={formField.onChange}
										/>
									) : null}
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				);

			default:
				return null;
		}
	};

	return (
		<Form {...form}>
			<form
				onSubmit={form.handleSubmit(handleSubmit, handleError)}
				className={cn("space-y-6", className)}
			>
				{currentFields.map(renderField)}

				{submitSuccess && (
					<div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative">
						Form submitted successfully!
					</div>
				)}
				{buttons ? (
					buttons
				) : (
					<div className="flex items-center justify-end space-x-2">
						{resetButton && (
							<Button
								type="button"
								variant="outline"
								onClick={() => form.reset()}
								disabled={isLoading}
							>
								{resetButtonText}
							</Button>
						)}
						<Button type="submit" disabled={isLoading}>
							{isLoading ? "Submitting..." : submitButtonText}
						</Button>
					</div>
				)}
			</form>
		</Form>
	);
};

const getFieldDefaultValue = (field: FieldConfig): any => {
	if (field.defaultValue !== undefined) {
		return field.defaultValue;
	}

	if (
		!field.required &&
		field.type !== "checkbox" &&
		field.type !== "switch" &&
		field.type !== "select"
	) {
		return undefined; // Return null for non-required fields without default value
	}

	switch (field.type) {
		case "checkbox":
			return [];
		case "color":
			return "#000000";
		case "switch":
			return false;
		case "date":
			return null;
		case "number":
			return 0;
		case "select":
		case "radio":
			// Nếu có options và field required, chọn option đầu tiên
			if (field.options && field.options.length > 0 && field.required) {
				return field.options[0].value;
			}
			return "";
		case "object":
			if (field.fields) {
				return field.fields.reduce(
					(objAcc: Record<string, any>, nestedField) => {
						objAcc[nestedField.name] = getFieldDefaultValue(nestedField);
						return objAcc;
					},
					{},
				);
			}
			return {};
		case "array":
			if (field.minItems && field.minItems > 0 && field.fields) {
				return Array.from({ length: field.minItems }).map(() =>
					field.fields?.reduce((itemAcc: Record<string, any>, itemField) => {
						itemAcc[itemField.name] = getFieldDefaultValue(itemField);
						return itemAcc;
					}, {}),
				);
			}
			return [];
		default:
			return "";
	}
};

const getColSpanClass = (colSpan?: number): string => {
	if (!colSpan || colSpan < 1 || colSpan > 12) return "col-span-12";

	const colSpanMap: Record<number, string> = {
		1: "col-span-1",
		2: "col-span-2",
		3: "col-span-3",
		4: "col-span-4",
		5: "col-span-5",
		6: "col-span-6",
		7: "col-span-7",
		8: "col-span-8",
		9: "col-span-9",
		10: "col-span-10",
		11: "col-span-11",
		12: "col-span-12",
	};

	return colSpanMap[colSpan] || "col-span-12";
};

// Helper function to get grid columns class
const getGridColsClass = (gridCols?: number): string => {
	if (!gridCols || gridCols < 1 || gridCols > 12) return "grid-cols-12";

	const gridColsMap: Record<number, string> = {
		1: "grid-cols-1",
		2: "grid-cols-2",
		3: "grid-cols-3",
		4: "grid-cols-4",
		5: "grid-cols-5",
		6: "grid-cols-6",
		7: "grid-cols-7",
		8: "grid-cols-8",
		9: "grid-cols-9",
		10: "grid-cols-10",
		11: "grid-cols-11",
		12: "grid-cols-12",
	};

	return gridColsMap[gridCols] || "grid-cols-12";
};

export default GeneralForm;
