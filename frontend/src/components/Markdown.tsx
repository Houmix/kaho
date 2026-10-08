import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

export default function Markdown({ children, className = '' }: { children: string; className?: string }) {
  return (
    <div className={`prose-kaho ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>{children}</ReactMarkdown>
    </div>
  );
}
