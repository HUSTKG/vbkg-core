import React, { useState, useEffect, useRef } from "react";
import { Search, X, Filter, History, Clock, Bookmark } from "lucide-react";
import { cn } from "../../lib/utils";

export interface SearchHistory {
	id: string | number;
	text: string;
	timestamp: string | Date;
}

export interface SearchBarProps {
	placeholder?: string;
	onSearch?: (query: string) => void;
	onChange?: (query: string) => void;
	onClear?: () => void;
	showFilter?: boolean;
	onFilterClick?: () => void;
	defaultHistory?: SearchHistory[];
	onHistoryItemClick?: (item: SearchHistory) => void;
	className?: string;
	initialValue?: string;
	loading?: boolean;
	saveHistory?: boolean;
	suggestions?: { label: string | number; value: any }[];
	autoFocus?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
	placeholder = "Tìm kiếm...",
	onSearch,
	onChange,
	onClear,
	showFilter = false,
	onFilterClick,
	defaultHistory = [],
	onHistoryItemClick,
	className,
	initialValue = "",
	loading = false,
	saveHistory = true,
	suggestions = [],
	autoFocus = false,
}) => {
	const [query, setQuery] = useState<string>(initialValue);
	const [showHistory, setShowHistory] = useState(false);
	const [localHistory, setLocalHistory] =
		useState<SearchHistory[]>(defaultHistory);
	const searchBarRef = useRef<HTMLDivElement>(null);
	const inputRef = useRef<HTMLInputElement>(null);

	// Update local defaultHistory when defaultHistory prop changes
	// useEffect(() => {
	//  setLocalHistory(defaultHistory);
	// }, [defaultHistory]);

	// Set focus on input when autoFocus is true
	useEffect(() => {
		if (autoFocus && inputRef.current) {
			inputRef.current.focus();
		}
	}, [autoFocus]);

	// Close defaultHistory dropdown when clicking outside
	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (
				searchBarRef.current &&
				!searchBarRef.current.contains(event.target as Node)
			) {
				setShowHistory(false);
			}
		};

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const value = e.target.value;
		setQuery(value);

		if (onChange) {
			onChange(value);
		}
	};

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();

		if (query.trim() && onSearch) {
			onSearch(query);

			if (saveHistory && query.trim()) {
				const newHistoryItem: SearchHistory = {
					id: Date.now(),
					text: query,
					timestamp: new Date().toISOString(),
				};

				// Check if this query already exists in defaultHistory
				const exists = localHistory.some(
					(item) => item.text.toLowerCase() === query.toLowerCase(),
				);

				if (!exists) {
					const updatedHistory = [newHistoryItem, ...localHistory.slice(0, 9)]; // Keep only most recent 10
					setLocalHistory(updatedHistory);
				}
			}

			setShowHistory(false);
		}
	};

	const handleClear = () => {
		setQuery("");
		if (onClear) {
			onClear();
		}
		if (inputRef.current) {
			inputRef.current.focus();
		}
	};

	const handleHistoryItemClick = (item: SearchHistory) => {
		setQuery(item.text);
		setShowHistory(false);

		if (onHistoryItemClick) {
			onHistoryItemClick(item);
		}

		if (onSearch) {
			onSearch(item.text);
		}
	};

	// Format time for display
	const formatTime = (time: string | Date): string => {
		const date = typeof time === "string" ? new Date(time) : time;
		const now = new Date();
		const diff = Math.floor((now.getTime() - date.getTime()) / 1000); // seconds

		if (diff < 60) {
			return "vừa xong";
		}

		const minutes = Math.floor(diff / 60);
		if (minutes < 60) {
			return `${minutes} phút trước`;
		}

		const hours = Math.floor(minutes / 60);
		if (hours < 24) {
			return `${hours} giờ trước`;
		}

		return date.toLocaleDateString();
	};

	// Filter relevant suggestions based on current query
	const filteredSuggestions = query
		? suggestions.filter((s) =>
				String(s.label).toLowerCase().includes(query.toLowerCase()),
			)
		: [];

	return (
		<div ref={searchBarRef} className={cn("relative", className)}>
			<form onSubmit={handleSubmit}>
				<div className="relative flex items-center">
					<div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
						{loading ? (
							<div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent" />
						) : (
							<Search size={18} className="text-gray-400 dark:text-gray-500" />
						)}
					</div>

					<input
						ref={inputRef}
						type="text"
						value={query}
						onChange={handleInputChange}
						placeholder={placeholder}
						className="w-full h-10 pl-10 pr-10 text-sm bg-gray-100 dark:bg-gray-700 border border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
						onFocus={() => (localHistory.length > 0 || filteredSuggestions.length > 0) && setShowHistory(true)}
					/>

					<div className="absolute inset-y-0 right-0 flex items-center pr-2">
						{query && (
							<button
								type="button"
								onClick={handleClear}
								className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
								aria-label="Clear search"
							>
								<X size={16} />
							</button>
						)}

						{showFilter && (
							<button
								type="button"
								onClick={onFilterClick}
								className="p-1 ml-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
								aria-label="Show filters"
							>
								<Filter size={16} />
							</button>
						)}
					</div>
				</div>
			</form>

			{/* Search defaultHistory and suggestions dropdown */}
			{showHistory &&
				(localHistory.length > 0 || filteredSuggestions.length > 0) && (
					<div className="absolute z-50 top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-10 max-h-80 overflow-y-auto">
						{localHistory.length > 0 && (
							<div>
								<div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
									<span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
										<History size={14} className="mr-1" />
										Lịch sử tìm kiếm
									</span>
									<button
										className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
										onClick={() => setLocalHistory([])}
									>
										Xóa tất cả
									</button>
								</div>
								<ul className="py-1">
									{localHistory.map((item) => (
										<li
											key={item.id}
											className="px-3 py-2 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
											onClick={() => handleHistoryItemClick(item)}
										>
											<div className="flex items-center">
												<Clock
													size={14}
													className="text-gray-400 dark:text-gray-500 mr-2"
												/>
												<span className="text-sm text-gray-700 dark:text-gray-300">
													{item.text}
												</span>
											</div>
											<span className="text-xs text-gray-400 dark:text-gray-500">
												{formatTime(item.timestamp)}
											</span>
										</li>
									))}
								</ul>
							</div>
						)}

						{filteredSuggestions.length > 0 && (
							<div>
								<div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700">
									<span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
										<Bookmark size={14} className="mr-1" />
										Gợi ý
									</span>
								</div>
								<ul className="py-1">
									{filteredSuggestions.map((suggestion, index) => (
										<li
											key={index}
											className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
											onClick={() => {
												setQuery(String(suggestion.label));
												setShowHistory(false);
												if (onSearch) {
													onSearch(suggestion.value);
												}
											}}
										>
											<div className="flex items-center">
												<Search
													size={14}
													className="text-gray-400 dark:text-gray-500 mr-2"
												/>
												<span className="text-sm text-gray-700 dark:text-gray-300">
													{suggestion.label}
												</span>
											</div>
										</li>
									))}
								</ul>
							</div>
						)}
					</div>
				)}
		</div>
	);
};

export default SearchBar;
