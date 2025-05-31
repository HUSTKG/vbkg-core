import { useState, useEffect, useRef, useMemo } from "react";
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Settings,
  Download,
  Plus,
  Search,
  Trash2,
  Edit,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Paperclip,
  Mic,
  MicOff,
  Zap,
  Database,
  FileText,
  BarChart3,
  Network,
  Brain,
  Lightbulb,
  X,
  Check,
  Star,
  Bookmark,
} from "lucide-react";

// Chat Message Component
const ChatMessage = ({
  message,
  onReact,
  onCopy,
  onEdit,
  onDelete,
  isLast,
}) => {
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.(message);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 group`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div
        className={`flex items-start space-x-2 max-w-[80%] ${isUser ? "flex-row-reverse space-x-reverse" : ""}`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? "bg-blue-500" : isSystem ? "bg-orange-500" : "bg-gray-600"
          }`}
        >
          {isUser ? (
            <User size={16} className="text-white" />
          ) : isSystem ? (
            <Settings size={16} className="text-white" />
          ) : (
            <Bot size={16} className="text-white" />
          )}
        </div>

        {/* Message Content */}
        <div
          className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
        >
          <div
            className={`p-3 rounded-lg max-w-full ${
              isUser
                ? "bg-blue-500 text-white"
                : isSystem
                  ? "bg-orange-100 border border-orange-200 text-orange-800"
                  : "bg-gray-100 border border-gray-200"
            }`}
          >
            {/* Message Type Indicator */}
            {message.type && (
              <div className="flex items-center space-x-1 mb-2 text-xs opacity-75">
                {message.type === "search_result" && <Search size={12} />}
                {message.type === "analysis" && <BarChart3 size={12} />}
                {message.type === "insight" && <Lightbulb size={12} />}
                <span className="capitalize">
                  {message.type.replace("_", " ")}
                </span>
              </div>
            )}

            {/* Message Content */}
            <div className="text-sm whitespace-pre-wrap">{message.content}</div>

            {/* Attachments */}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2 space-y-1">
                {message.attachments.map((attachment, idx) => (
                  <div
                    key={idx}
                    className="flex items-center space-x-2 text-xs opacity-75"
                  >
                    <FileText size={12} />
                    <span>{attachment.name}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Knowledge Graph References */}
            {message.references && message.references.length > 0 && (
              <div className="mt-2 pt-2 border-t border-opacity-20 border-current">
                <div className="text-xs opacity-75 mb-1">
                  Referenced entities:
                </div>
                <div className="flex flex-wrap gap-1">
                  {message.references.map((ref, idx) => (
                    <span
                      key={idx}
                      className="inline-block px-2 py-1 bg-black bg-opacity-10 rounded text-xs"
                    >
                      {ref.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence Score */}
            {message.confidence && (
              <div className="mt-2 text-xs opacity-75">
                Confidence: {(message.confidence * 100).toFixed(1)}%
              </div>
            )}
          </div>

          {/* Message Footer */}
          <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
            <span>{formatTime(message.timestamp)}</span>
            {message.edited && <span className="italic">(edited)</span>}

            {/* Message Actions */}
            {showActions && (
              <div className="flex items-center space-x-1 ml-2">
                <button
                  onClick={handleCopy}
                  className="p-1 hover:bg-gray-200 rounded"
                  title="Copy message"
                >
                  {copied ? (
                    <Check size={12} className="text-green-500" />
                  ) : (
                    <Copy size={12} />
                  )}
                </button>

                {!isUser && (
                  <>
                    <button
                      onClick={() => onReact?.(message, "like")}
                      className={`p-1 hover:bg-gray-200 rounded ${message.userReaction === "like" ? "text-green-500" : ""}`}
                      title="Like message"
                    >
                      <ThumbsUp size={12} />
                    </button>
                    <button
                      onClick={() => onReact?.(message, "dislike")}
                      className={`p-1 hover:bg-gray-200 rounded ${message.userReaction === "dislike" ? "text-red-500" : ""}`}
                      title="Dislike message"
                    >
                      <ThumbsDown size={12} />
                    </button>
                  </>
                )}

                {isUser && (
                  <button
                    onClick={() => onEdit?.(message)}
                    className="p-1 hover:bg-gray-200 rounded"
                    title="Edit message"
                  >
                    <Edit size={12} />
                  </button>
                )}

                <button
                  onClick={() => onDelete?.(message)}
                  className="p-1 hover:bg-gray-200 rounded text-red-500"
                  title="Delete message"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Quick Actions Panel
const QuickActionsPanel = ({ onSelectAction, isVisible, onToggle }) => {
  const quickActions = [
    {
      id: "search_entities",
      label: "Search Entities",
      icon: <Search size={16} />,
      prompt: "Search for entities related to: ",
      category: "search",
    },
    {
      id: "analyze_relationships",
      label: "Analyze Relationships",
      icon: <Network size={16} />,
      prompt: "Analyze relationships between: ",
      category: "analysis",
    },
    {
      id: "find_insights",
      label: "Find Insights",
      icon: <Lightbulb size={16} />,
      prompt: "Find insights about: ",
      category: "insights",
    },
    {
      id: "compare_entities",
      label: "Compare Entities",
      icon: <BarChart3 size={16} />,
      prompt: "Compare these entities: ",
      category: "analysis",
    },
    {
      id: "generate_report",
      label: "Generate Report",
      icon: <FileText size={16} />,
      prompt: "Generate a report about: ",
      category: "reporting",
    },
    {
      id: "explore_graph",
      label: "Explore Graph",
      icon: <Database size={16} />,
      prompt: "Explore the knowledge graph around: ",
      category: "exploration",
    },
  ];

  if (!isVisible) return null;

  const categories = [
    ...new Set(quickActions.map((action) => action.category)),
  ];

  return (
    <div className="bg-white border rounded-lg shadow-lg p-4 absolute bottom-full left-0 right-0 mb-2 z-10">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Quick Actions</h3>
        <button onClick={onToggle} className="p-1 hover:bg-gray-100 rounded">
          <X size={16} />
        </button>
      </div>

      {categories.map((category) => (
        <div key={category} className="mb-3 last:mb-0">
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2 capitalize">
            {category}
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {quickActions
              .filter((action) => action.category === category)
              .map((action) => (
                <button
                  key={action.id}
                  onClick={() => onSelectAction(action)}
                  className="flex items-center space-x-2 p-2 text-sm border rounded hover:bg-gray-50 text-left"
                >
                  {action.icon}
                  <span>{action.label}</span>
                </button>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// Chat Input Component
const ChatInput = ({ onSend, isLoading, onUploadFile }) => {
  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const textareaRef = useRef(null);

  const handleSend = () => {
    if (message.trim() || attachments.length > 0) {
      onSend({
        content: message.trim(),
        attachments: attachments,
        timestamp: new Date(),
      });
      setMessage("");
      setAttachments([]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const newAttachments = files.map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type,
      file: file,
    }));
    setAttachments((prev) => [...prev, ...newAttachments]);
    onUploadFile?.(files);
  };

  const removeAttachment = (index) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleQuickAction = (action) => {
    setMessage(action.prompt);
    setShowQuickActions(false);
    textareaRef.current?.focus();
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  return (
    <div className="relative">
      <QuickActionsPanel
        isVisible={showQuickActions}
        onToggle={() => setShowQuickActions(!showQuickActions)}
        onSelectAction={handleQuickAction}
      />

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="mb-2 p-2 bg-gray-50 rounded-lg">
          <div className="flex flex-wrap gap-2">
            {attachments.map((attachment, idx) => (
              <div
                key={idx}
                className="flex items-center space-x-2 bg-white px-2 py-1 rounded border"
              >
                <FileText size={14} />
                <span className="text-sm">{attachment.name}</span>
                <button
                  onClick={() => removeAttachment(idx)}
                  className="text-red-500 hover:text-red-700"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-end space-x-2 p-3 bg-gray-50 rounded-lg">
        {/* Quick Actions Button */}
        <button
          onClick={() => setShowQuickActions(!showQuickActions)}
          className={`p-2 rounded-lg hover:bg-gray-200 ${showQuickActions ? "bg-blue-100 text-blue-600" : "text-gray-500"}`}
          title="Quick Actions"
        >
          <Zap size={18} />
        </button>

        {/* File Upload */}
        <label
          className="p-2 rounded-lg hover:bg-gray-200 text-gray-500 cursor-pointer"
          title="Attach File"
        >
          <Paperclip size={18} />
          <input
            type="file"
            multiple
            onChange={handleFileUpload}
            className="hidden"
            accept=".txt,.pdf,.doc,.docx,.json,.csv"
          />
        </label>

        {/* Voice Recording */}
        <button
          onClick={() => setIsRecording(!isRecording)}
          className={`p-2 rounded-lg hover:bg-gray-200 ${isRecording ? "text-red-500 bg-red-100" : "text-gray-500"}`}
          title={isRecording ? "Stop Recording" : "Voice Input"}
        >
          {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
        </button>

        {/* Message Input */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about the knowledge graph..."
          className="flex-1 resize-none border-0 bg-transparent focus:outline-none max-h-32 min-h-[20px]"
          disabled={isLoading}
          rows={1}
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={isLoading || (!message.trim() && attachments.length === 0)}
          className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Send Message"
        >
          {isLoading ? (
            <RefreshCw size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>
    </div>
  );
};

// Conversation History Sidebar
const ConversationSidebar = ({
  conversations,
  activeConversation,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) => {
  const [filter, setFilter] = useState("");

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="w-80 bg-white self-stretch border-r border-gray-200">
      <div className="w-80 h-full bg-white self-stretch border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 sticky top-0 bg-white/95">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Conversations</h2>
            <button
              onClick={onNewConversation}
              className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              title="New Conversation"
            >
              <Plus size={16} />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <MessageSquare size={24} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations found</p>
            </div>
          ) : (
            <div className="p-2">
              {filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => onSelectConversation(conversation)}
                  className={`p-3 rounded-lg cursor-pointer mb-2 group hover:bg-gray-50 ${
                    activeConversation?.id === conversation.id
                      ? "bg-blue-50 border-blue-200 border"
                      : "border border-transparent"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate mb-1">
                        {conversation.title}
                      </h3>
                      <p className="text-xs text-gray-500 truncate">
                        {conversation.lastMessage}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <time className="text-xs text-gray-400">
                          {new Date(
                            conversation.updatedAt,
                          ).toLocaleDateString()}
                        </time>
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-400">
                            {conversation.messageCount} messages
                          </span>
                          {conversation.isBookmarked && (
                            <Bookmark size={12} className="text-yellow-500" />
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // Toggle bookmark
                        }}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="Bookmark"
                      >
                        <Star size={12} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conversation.id);
                        }}
                        className="p-1 hover:bg-gray-200 rounded text-red-500"
                        title="Delete Conversation"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Settings Modal
const SettingsModal = ({ isOpen, onClose, settings, onUpdateSettings }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-1">
      <div className="bg-white rounded-lg max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Chat Settings</h2>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* AI Model Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">AI Model</label>
            <select
              value={localSettings.model}
              onChange={(e) =>
                setLocalSettings((prev) => ({ ...prev, model: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="gpt-4">GPT-4 (Recommended)</option>
              <option value="gpt-3.5">GPT-3.5 Turbo</option>
              <option value="claude">Claude-3</option>
            </select>
          </div>

          {/* Response Style */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Response Style
            </label>
            <select
              value={localSettings.responseStyle}
              onChange={(e) =>
                setLocalSettings((prev) => ({
                  ...prev,
                  responseStyle: e.target.value,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="detailed">Detailed</option>
              <option value="concise">Concise</option>
              <option value="academic">Academic</option>
              <option value="casual">Casual</option>
            </select>
          </div>

          {/* Features */}
          <div className="space-y-3">
            <label className="block text-sm font-medium">Features</label>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoSave"
                checked={localSettings.autoSave}
                onChange={(e) =>
                  setLocalSettings((prev) => ({
                    ...prev,
                    autoSave: e.target.checked,
                  }))
                }
              />
              <label htmlFor="autoSave" className="text-sm">
                Auto-save conversations
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="showConfidence"
                checked={localSettings.showConfidence}
                onChange={(e) =>
                  setLocalSettings((prev) => ({
                    ...prev,
                    showConfidence: e.target.checked,
                  }))
                }
              />
              <label htmlFor="showConfidence" className="text-sm">
                Show confidence scores
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="enableVoice"
                checked={localSettings.enableVoice}
                onChange={(e) =>
                  setLocalSettings((prev) => ({
                    ...prev,
                    enableVoice: e.target.checked,
                  }))
                }
              />
              <label htmlFor="enableVoice" className="text-sm">
                Enable voice input
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="contextualSuggestions"
                checked={localSettings.contextualSuggestions}
                onChange={(e) =>
                  setLocalSettings((prev) => ({
                    ...prev,
                    contextualSuggestions: e.target.checked,
                  }))
                }
              />
              <label htmlFor="contextualSuggestions" className="text-sm">
                Show contextual suggestions
              </label>
            </div>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Creativity Level: {localSettings.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={localSettings.temperature}
              onChange={(e) =>
                setLocalSettings((prev) => ({
                  ...prev,
                  temperature: parseFloat(e.target.value),
                }))
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onUpdateSettings(localSettings);
              onClose();
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Research Chatbot Component
const ResearchChatbotPage = () => {
  // State Management
  const [conversations, setConversations] = useState([
    {
      id: "1",
      title: "Apple Inc. Analysis",
      lastMessage: "What are the key relationships for Apple Inc.?",
      messageCount: 12,
      updatedAt: new Date("2024-01-25T10:30:00Z"),
      isBookmarked: true,
      messages: [],
    },
    {
      id: "2",
      title: "Tech Companies Comparison",
      lastMessage: "Compare Apple, Microsoft, and Google",
      messageCount: 8,
      updatedAt: new Date("2024-01-24T15:45:00Z"),
      isBookmarked: false,
      messages: [],
    },
  ]);

  const [activeConversation, setActiveConversation] = useState(
    conversations[0],
  );
  const [messages, setMessages] = useState([
    {
      id: "1",
      role: "system",
      content:
        "Welcome to the Knowledge Graph Research Assistant! I can help you explore entities, relationships, and insights from the knowledge graph. What would you like to research today?",
      timestamp: new Date("2024-01-25T10:00:00Z"),
      type: "system",
    },
    {
      id: "2",
      role: "user",
      content: "Tell me about Apple Inc. and its key relationships",
      timestamp: new Date("2024-01-25T10:01:00Z"),
    },
    {
      id: "3",
      role: "assistant",
      content:
        "Based on the knowledge graph, Apple Inc. is a major technology company with several key relationships:\n\n• **Leadership**: Tim Cook serves as CEO since 2011\n• **Products**: Produces iPhone, iPad, Mac, and other devices\n• **Competitors**: Competes with Microsoft, Google, Samsung\n• **Partnerships**: Has partnerships with suppliers like TSMC, Foxconn\n\nI found 15 direct relationships and 200+ connected entities. Would you like me to explore any specific aspect deeper?",
      timestamp: new Date("2024-01-25T10:01:30Z"),
      type: "analysis",
      confidence: 0.94,
      references: [
        { id: "1", name: "Apple Inc.", type: "Company" },
        { id: "2", name: "Tim Cook", type: "Person" },
        { id: "3", name: "iPhone", type: "Product" },
      ],
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    model: "gpt-4",
    responseStyle: "detailed",
    temperature: 0.7,
    autoSave: true,
    showConfidence: true,
    enableVoice: false,
    contextualSuggestions: true,
  });

  const messagesEndRef = useRef(null);

  // Statistics
  const stats = useMemo(
    () => ({
      totalConversations: conversations.length,
      totalMessages: conversations.reduce(
        (sum, conv) => sum + conv.messageCount,
        0,
      ),
      avgResponseTime: "1.2s",
      userSatisfaction: "4.8/5",
    }),
    [conversations],
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle sending message
  const handleSendMessage = async (messageData) => {
    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageData.content,
      timestamp: messageData.timestamp,
      attachments: messageData.attachments,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateAIResponse(messageData.content),
        timestamp: new Date(),
        type: detectMessageType(messageData.content),
        confidence: Math.random() * 0.3 + 0.7, // 0.7-1.0
        references: generateReferences(messageData.content),
      };

      setMessages((prev) => [...prev, aiResponse]);
      setIsLoading(false);

      // Update conversation
      updateConversationLastMessage(userMessage.content);
    }, 1500);
  };

  // Generate AI response based on message content
  const generateAIResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes("search") || lowerMessage.includes("find")) {
      return `I've searched the knowledge graph and found ${Math.floor(Math.random() * 50) + 10} relevant entities. Here are the top results:\n\n• **Entity 1**: High confidence match (95%)\n• **Entity 2**: Medium confidence match (78%)\n• **Entity 3**: Related entity (82%)\n\nWould you like me to explore any of these in detail or refine the search?`;
    }

    if (
      lowerMessage.includes("relationship") ||
      lowerMessage.includes("connect")
    ) {
      return `I've analyzed the relationships in the knowledge graph:\n\n**Direct Relationships**: ${Math.floor(Math.random() * 10) + 5}\n**Indirect Connections**: ${Math.floor(Math.random() * 30) + 20}\n**Relationship Types**: CEO_OF, PRODUCES, COMPETES_WITH, PARTNERS_WITH\n\nThe strongest connections are through business partnerships and competitive relationships. Shall I visualize this network for you?`;
    }

    if (lowerMessage.includes("compare") || lowerMessage.includes("versus")) {
      return `Based on the knowledge graph analysis, here's a comparison:\n\n**Similarities**:\n• Both operate in technology sector\n• Similar revenue ranges\n• Competitive relationship\n\n**Differences**:\n• Different product focus areas\n• Distinct market strategies\n• Varying partnership networks\n\nThe confidence score for this comparison is 89%. Would you like a detailed breakdown of any specific aspect?`;
    }

    if (lowerMessage.includes("insight") || lowerMessage.includes("analysis")) {
      return `From analyzing the knowledge graph patterns, I've identified several key insights:\n\n🔍 **Market Dynamics**: Strong clustering around tech ecosystem\n📊 **Relationship Patterns**: Hub-and-spoke model with major companies as centers\n💡 **Emerging Trends**: Increasing AI and sustainability connections\n\nConfidence level: 92%. These insights are based on ${Math.floor(Math.random() * 1000) + 500} entity relationships. Want me to dive deeper into any specific area?`;
    }

    return `I've processed your query against the knowledge graph. Based on the available data, I found ${Math.floor(Math.random() * 20) + 5} relevant connections and ${Math.floor(Math.random() * 50) + 15} related entities.\n\nKey findings:\n• High-confidence matches: ${Math.floor(Math.random() * 5) + 2}\n• Related concepts: ${Math.floor(Math.random() * 10) + 5}\n• Confidence score: ${(Math.random() * 0.3 + 0.7).toFixed(2)}\n\nWhat specific aspect would you like me to explore further?`;
  };

  // Detect message type for AI responses
  const detectMessageType = (content) => {
    const lowerContent = content.toLowerCase();
    if (lowerContent.includes("search") || lowerContent.includes("find"))
      return "search_result";
    if (lowerContent.includes("analyze") || lowerContent.includes("analysis"))
      return "analysis";
    if (lowerContent.includes("insight") || lowerContent.includes("trend"))
      return "insight";
    if (lowerContent.includes("compare") || lowerContent.includes("versus"))
      return "comparison";
    return "response";
  };

  // Generate mock references
  const generateReferences = (content) => {
    const possibleRefs = [
      { id: "1", name: "Apple Inc.", type: "Company" },
      { id: "2", name: "Microsoft Corporation", type: "Company" },
      { id: "3", name: "Tim Cook", type: "Person" },
      { id: "4", name: "iPhone", type: "Product" },
      { id: "5", name: "Technology Sector", type: "Category" },
    ];

    return possibleRefs.slice(0, Math.floor(Math.random() * 3) + 1);
  };

  // Update conversation's last message
  const updateConversationLastMessage = (message) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversation.id
          ? {
              ...conv,
              lastMessage:
                message.slice(0, 50) + (message.length > 50 ? "..." : ""),
              messageCount: conv.messageCount + 2, // user + ai message
              updatedAt: new Date(),
            }
          : conv,
      ),
    );
  };

  // Handle conversation selection
  const handleSelectConversation = (conversation) => {
    setActiveConversation(conversation);
    // In real app, load messages for this conversation
    // For demo, keeping current messages
  };

  // Handle new conversation
  const handleNewConversation = () => {
    const newConversation = {
      id: Date.now().toString(),
      title: `New Chat ${conversations.length + 1}`,
      lastMessage: "",
      messageCount: 0,
      updatedAt: new Date(),
      isBookmarked: false,
      messages: [],
    };

    setConversations((prev) => [newConversation, ...prev]);
    setActiveConversation(newConversation);
    setMessages([
      {
        id: Date.now().toString(),
        role: "system",
        content:
          "New conversation started. How can I help you explore the knowledge graph?",
        timestamp: new Date(),
        type: "system",
      },
    ]);
  };

  // Handle conversation deletion
  const handleDeleteConversation = (conversationId) => {
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      setConversations((prev) =>
        prev.filter((conv) => conv.id !== conversationId),
      );

      if (
        activeConversation.id === conversationId &&
        conversations.length > 1
      ) {
        const remainingConversations = conversations.filter(
          (conv) => conv.id !== conversationId,
        );
        setActiveConversation(remainingConversations[0]);
      }
    }
  };

  // Handle message reactions
  const handleMessageReaction = (message, reaction) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === message.id
          ? {
              ...msg,
              userReaction: msg.userReaction === reaction ? null : reaction,
            }
          : msg,
      ),
    );
  };

  // Handle message deletion
  const handleDeleteMessage = (message) => {
    if (window.confirm("Are you sure you want to delete this message?")) {
      setMessages((prev) => prev.filter((msg) => msg.id !== message.id));
    }
  };

  // Export conversation
  const handleExportConversation = () => {
    const exportData = {
      conversation: activeConversation,
      messages: messages,
      exportedAt: new Date(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation-${activeConversation.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen items-stretch bg-gray-50 flex">
      {/* Conversation Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        activeConversation={activeConversation}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white self-stretch z-50 border-b border-gray-200 p-4 sticky top-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Brain size={24} className="text-blue-600" />
              <div>
                <h1 className="text-lg font-semibold">
                  {activeConversation.title}
                </h1>
                <p className="text-sm text-gray-500">
                  AI Research Assistant • Knowledge Graph Explorer
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Statistics */}
              <div className="hidden md:flex items-center space-x-4 text-sm text-gray-500 mr-4">
                <span>{stats.totalMessages} messages</span>
                <span>{stats.avgResponseTime} avg response</span>
                <span>⭐ {stats.userSatisfaction}</span>
              </div>

              <button
                onClick={handleExportConversation}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title="Export Conversation"
              >
                <Download size={18} />
              </button>

              <button
                onClick={() => setShowSettings(true)}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title="Chat Settings"
              >
                <Settings size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onReact={handleMessageReaction}
              onDelete={handleDeleteMessage}
              isLast={message.id === messages[messages.length - 1]?.id}
            />
          ))}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isLoading}
            onUploadFile={(files) => console.log("Files uploaded:", files)}
          />
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onUpdateSettings={setSettings}
      />
    </div>
  );
};

export default ResearchChatbotPage;
