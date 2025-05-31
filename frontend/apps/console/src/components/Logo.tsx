export const Logo = () => {
	return (
		<div className="flex items-center">
			<svg
				width="40"
				height="40"
				viewBox="0 0 40 40"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<rect width="40" height="40" rx="8" fill="#3B82F6" />
				<circle cx="12" cy="12" r="4" fill="white" />
				<circle cx="28" cy="12" r="4" fill="white" />
				<circle cx="12" cy="28" r="4" fill="white" />
				<circle cx="28" cy="28" r="4" fill="white" />
				<path d="M12 12L28 28" stroke="white" strokeWidth="2" />
				<path d="M28 12L12 28" stroke="white" strokeWidth="2" />
				<path d="M12 12L28 12" stroke="white" strokeWidth="2" />
				<path d="M12 28L28 28" stroke="white" strokeWidth="2" />
				<path d="M12 12L12 28" stroke="white" strokeWidth="2" />
				<path d="M28 12L28 28" stroke="white" strokeWidth="2" />
			</svg>
			<div className="ml-3">
				<h1 className="text-xl font-bold text-gray-900 dark:text-white">Knowledge Graph UI</h1>
				<p className="text-sm text-gray-600 dark:text-gray-400">Component Library</p>
			</div>
		</div>
	);
};

export default Logo;
