 import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import ChatMessage from './ChatMessage';
import { useChatbot } from '../hooks/useChatbot';

interface ChatbotProps {
  patientId: bigint;
}

export default function Chatbot({ patientId }: ChatbotProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const { messages, sendMessage, isLoading } = useChatbot(patientId);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="animate-fade-in rounded-2xl border-2 border-border bg-card/80 backdrop-blur-sm shadow-medical-lg transition-all duration-300 hover:shadow-medical-xl">
      <div className="border-b border-border p-6">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-medical-primary/10 p-2 transition-all duration-300 hover:bg-medical-primary/20">
            <img
              src="/assets/generated/chatbot-icon.dim_128x128.png"
              alt="AI Assistant"
              className="h-8 w-8"
            />
          </div>
          <div>
            <h3 className="text-xl font-semibold">AI Medical Assistant</h3>
            <p className="text-sm text-muted-foreground">
              Ask questions about your pharmacogenomic results
            </p>
          </div>
        </div>
      </div>

      <Alert className="m-6 border-yellow-500/50 bg-yellow-500/10">
        <AlertCircle className="h-4 w-4 text-yellow-600" />
        <AlertDescription className="text-sm text-yellow-800 dark:text-yellow-200">
          <strong>Medical Disclaimer:</strong> This AI assistant provides educational information
          only and is not a substitute for professional medical advice, diagnosis, or treatment.
          Always consult with qualified healthcare providers.
        </AlertDescription>
      </Alert>

      <ScrollArea className="h-96 px-6" ref={scrollRef}>
        <div className="space-y-4 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Bot className="mb-4 h-12 w-12 text-muted-foreground animate-pulse" />
              <p className="text-sm text-muted-foreground mb-2">
                Start a conversation by asking about your results
              </p>
              <p className="text-xs text-muted-foreground max-w-md">
                Example: "What does my CYP2D6 genotype mean?" or "Why is dose adjustment recommended?"
              </p>
            </div>
          )}
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-border p-6">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your results, genes, or medications..."
            disabled={isLoading}
            className="flex-1 transition-all duration-300 focus:border-medical-primary"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
