export interface CommentItem {
  id: string;
  author_name: string;
  author_email: string;
  homepage: string;
  text: string;
  parent_id: string | null;
  root_id: string;
  depth: number;
  created_at: string;
  has_more_replies: boolean;
  replies: CommentItem[];
}

export interface CommentPage {
  next: string | null;
  previous: string | null;
  results: CommentItem[];
}

export interface CommentDraft {
  username: string;
  email: string;
  homepage: string;
  text: string;
}
