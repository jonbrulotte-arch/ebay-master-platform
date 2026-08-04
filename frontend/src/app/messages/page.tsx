"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Mail, MailOpen, RefreshCw, Send } from "lucide-react";

interface Message {
  id: string;
  order_id: string | null;
  buyer_username: string;
  direction: "INBOUND" | "OUTBOUND";
  subject: string | null;
  body: string | null;
  is_read: boolean;
  responded_at: string | null;
  created_at: string;
}

function useMessages(isRead?: boolean) {
  return useQuery<{ items: Message[]; total: number }>({
    queryKey: ["messages", isRead],
    queryFn: async () => {
      const { data } = await apiClient.get("/messages", {
        params: isRead !== undefined ? { is_read: isRead } : {},
      });
      return data;
    },
  });
}

function useMarkRead() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await apiClient.patch(`/messages/${id}/read`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await apiClient.post("/messages/read-all");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

function useSendReply() {
  const qc = useQueryClient();
  return useMutation<Message, Error, { buyer_username: string; order_id: string | null; subject: string; body: string }>({
    mutationFn: async (body) => {
      const { data } = await apiClient.post("/messages", body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

function MessageRow({
  msg,
  selected,
  onClick,
}: {
  msg: Message;
  selected: boolean;
  onClick: () => void;
}) {
  const markRead = useMarkRead();
  const isInbound = msg.direction === "INBOUND";

  return (
    <div
      onClick={() => {
        onClick();
        if (!msg.is_read && isInbound) markRead.mutate(msg.id);
      }}
      className={`flex items-start gap-3 p-4 cursor-pointer border-b transition-colors ${
        selected ? "bg-blue-50" : "hover:bg-gray-50"
      } ${!msg.is_read && isInbound ? "font-medium" : ""}`}
    >
      <div className={`mt-0.5 ${!msg.is_read && isInbound ? "text-blue-600" : "text-gray-400"}`}>
        {msg.is_read || !isInbound ? <MailOpen size={16} /> : <Mail size={16} />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm truncate">{msg.buyer_username}</p>
          <p className="text-xs text-gray-400 shrink-0">
            {new Date(msg.created_at).toLocaleDateString()}
          </p>
        </div>
        <p className="text-xs text-gray-500 truncate">{msg.subject || "(no subject)"}</p>
        <p className="text-xs text-gray-400 truncate mt-0.5">{msg.body?.slice(0, 80)}</p>
      </div>
      <span
        className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
          isInbound ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"
        }`}
      >
        {isInbound ? "In" : "Out"}
      </span>
    </div>
  );
}

function ReplyPanel({
  message,
  onClose,
}: {
  message: Message;
  onClose: () => void;
}) {
  const sendReply = useSendReply();
  const [replyBody, setReplyBody] = useState("");

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!replyBody.trim()) return;
    sendReply.mutate(
      {
        buyer_username: message.buyer_username,
        order_id: message.order_id,
        subject: `Re: ${message.subject || ""}`,
        body: replyBody,
      },
      {
        onSuccess: () => {
          setReplyBody("");
        },
      }
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b px-4 py-3 flex items-center justify-between">
        <div>
          <p className="font-medium text-gray-800">{message.buyer_username}</p>
          <p className="text-xs text-gray-500">{message.subject || "(no subject)"}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-sm">
          Close
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div
          className={`rounded-lg p-3 text-sm mb-3 max-w-sm ${
            message.direction === "INBOUND"
              ? "bg-gray-100 text-gray-800 mr-auto"
              : "bg-blue-600 text-white ml-auto"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.body || "(no content)"}</p>
          <p className={`text-xs mt-1 ${message.direction === "INBOUND" ? "text-gray-400" : "text-blue-200"}`}>
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
      </div>

      <form onSubmit={handleSend} className="border-t p-3 flex gap-2">
        <textarea
          rows={2}
          placeholder="Type your reply…"
          value={replyBody}
          onChange={(e) => setReplyBody(e.target.value)}
          className="flex-1 border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!replyBody.trim() || sendReply.isPending}
          className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1 text-sm"
        >
          <Send size={14} />
          {sendReply.isPending ? "Sending…" : "Send"}
        </button>
      </form>
    </div>
  );
}

export default function MessagesPage() {
  const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined);
  const [selected, setSelected] = useState<Message | null>(null);
  const { data, isLoading, refetch } = useMessages(filterRead);
  const markAllRead = useMarkAllRead();

  const messages = data?.items ?? [];
  const unread = messages.filter((m) => !m.is_read && m.direction === "INBOUND").length;

  return (
    <div className="flex gap-0 h-[calc(100vh-140px)] -mx-6 -my-0">
      {/* Message list */}
      <div className="w-80 border-r bg-white flex flex-col shrink-0">
        <div className="p-3 border-b flex items-center justify-between gap-2">
          <div className="flex gap-1">
            {([undefined, false, true] as const).map((val) => (
              <button
                key={String(val)}
                onClick={() => setFilterRead(val)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  filterRead === val
                    ? "bg-blue-600 text-white"
                    : "border hover:bg-gray-50 text-gray-600"
                }`}
              >
                {val === undefined ? "All" : val ? "Read" : `Unread${unread > 0 ? ` (${unread})` : ""}`}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => markAllRead.mutate()}
              title="Mark all read"
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <MailOpen size={14} />
            </button>
            <button
              onClick={() => refetch()}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-14 bg-gray-50 rounded animate-pulse" />
              ))}
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 p-6">
              <Mail size={32} className="mb-2" />
              <p className="text-sm">No messages</p>
            </div>
          ) : (
            messages.map((m) => (
              <MessageRow
                key={m.id}
                msg={m}
                selected={selected?.id === m.id}
                onClick={() => setSelected(m)}
              />
            ))
          )}
        </div>
      </div>

      {/* Detail pane */}
      <div className="flex-1 bg-white">
        {selected ? (
          <ReplyPanel message={selected} onClose={() => setSelected(null)} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Mail size={40} className="mb-3" />
            <p className="text-sm">Select a message to view</p>
          </div>
        )}
      </div>
    </div>
  );
}
