import { computed, readonly, ref } from "vue";

export const Locale = {
  English: "en",
  Ukrainian: "uk",
  Russian: "ru",
} as const;

export type Locale = (typeof Locale)[keyof typeof Locale];

const STORAGE_KEY = "threadflow-locale";

const english = {
  tagline: "Thoughtful conversations, clearly connected.",
  joinDiscussion: "Join the discussion",
  joinHint: "Share a thought or ask a question",
  comments: "Comments",
  live: "Live",
  connecting: "Connecting",
  closed: "Offline",
  sortField: "Sort field",
  sortDirection: "Sort direction",
  date: "Date",
  name: "Name",
  email: "Email",
  descending: "Newest first",
  ascending: "Oldest first",
  newComments: "{count} new comments",
  loading: "Loading…",
  emptyThread: "No comments yet. Start the conversation.",
  loadMoreComments: "Load 25 more comments",
  theme: "Theme",
  auto: "Auto",
  light: "Light",
  dark: "Dark",
  language: "Language",
  signIn: "Sign in",
  register: "Register",
  signOut: "Sign out",
  changeAvatar: "Change avatar",
  welcomeBack: "Welcome back",
  createAccount: "Create account",
  usernameOrEmail: "Username or email",
  username: "Username",
  password: "Password",
  pleaseWait: "Please wait…",
  close: "Close",
  addComment: "Add comment",
  replyTo: "Reply to {name}",
  cancel: "Cancel",
  postingAs: "Posting as",
  homepage: "Homepage",
  comment: "Comment",
  write: "Write",
  preview: "Preview",
  formatting: "Formatting",
  bold: "Bold",
  italic: "Italic",
  code: "Code",
  link: "Link",
  linkUrl: "Link URL",
  commentPlaceholder: "Write a thoughtful reply…",
  characters: "{count} characters",
  previewFailed: "Preview failed — check that your tags are closed.",
  attachment: "Attachment",
  attachmentHint: "JPG, PNG, GIF or TXT",
  chooseFile: "Choose file",
  removeAttachment: "Remove attachment",
  uploadFailed: "Unable to upload the attachment.",
  captcha: "CAPTCHA",
  captchaAlt: "CAPTCHA challenge",
  captchaLoading: "Loading CAPTCHA…",
  captchaUnavailable: "CAPTCHA unavailable",
  newImage: "New image",
  sendComment: "Send comment",
  sending: "Sending…",
  copyLink: "Copy link",
  linkCopied: "Link copied",
  reply: "Reply",
  upvote: "Upvote",
  downvote: "Downvote",
  loadingPreview: "Loading preview…",
  textPreviewFailed: "Unable to load text preview",
  loadMoreReplies: "Load more replies",
  searchPlaceholder: "Search comments and authors…",
  searchQuery: "Search query",
  search: "Search",
  filters: "Filters",
  author: "Author",
  nameOrEmail: "Name or email",
  fromDate: "From date",
  toDate: "To date",
  sortBy: "Sort by",
  relevance: "Relevance",
  direction: "Direction",
  applyFilters: "Apply filters",
  reset: "Reset",
  searching: "Searching…",
  resultsLoaded: "{count} loaded",
  moreAvailable: "more available",
  source: "source",
  searchCriteriaError: "Enter at least two characters or choose a filter.",
  searchUnavailable: "Search is temporarily unavailable.",
  noQueryMatches: "No matches for “{query}”.",
  noFilterMatches: "No matches for the selected filters.",
  loadMoreResults: "Load more results",
} as const;

type MessageKey = keyof typeof english;
type Messages = Record<MessageKey, string>;

const ukrainian: Messages = {
  tagline: "Змістовні розмови зі зрозумілими зв’язками.", joinDiscussion: "Долучитися до обговорення", joinHint: "Поділіться думкою або поставте запитання", comments: "Коментарі", live: "Наживо", connecting: "Підключення", closed: "Офлайн", sortField: "Поле сортування", sortDirection: "Напрямок сортування", date: "Дата", name: "Ім’я", email: "Email", descending: "Спочатку нові", ascending: "Спочатку старі", newComments: "Нових коментарів: {count}", loading: "Завантаження…", emptyThread: "Коментарів ще немає. Почніть розмову.", loadMoreComments: "Завантажити ще 25 коментарів", theme: "Тема", auto: "Авто", light: "Світла", dark: "Темна", language: "Мова", signIn: "Увійти", register: "Реєстрація", signOut: "Вийти", changeAvatar: "Змінити аватар", welcomeBack: "З поверненням", createAccount: "Створити акаунт", usernameOrEmail: "Ім’я або email", username: "Ім’я користувача", password: "Пароль", pleaseWait: "Зачекайте…", close: "Закрити", addComment: "Додати коментар", replyTo: "Відповідь для {name}", cancel: "Скасувати", postingAs: "Ви пишете як", homepage: "Сайт", comment: "Коментар", write: "Написати", preview: "Перегляд", formatting: "Форматування", bold: "Жирний", italic: "Курсив", code: "Код", link: "Посилання", linkUrl: "Адреса посилання", commentPlaceholder: "Напишіть змістовну відповідь…", characters: "Символів: {count}", previewFailed: "Не вдалося створити перегляд — перевірте закриття тегів.", attachment: "Вкладення", attachmentHint: "JPG, PNG, GIF або TXT", chooseFile: "Обрати файл", removeAttachment: "Видалити вкладення", uploadFailed: "Не вдалося завантажити вкладення.", captcha: "CAPTCHA", captchaAlt: "Зображення CAPTCHA", captchaLoading: "CAPTCHA завантажується…", captchaUnavailable: "CAPTCHA недоступна", newImage: "Нове зображення", sendComment: "Надіслати коментар", sending: "Надсилання…", copyLink: "Копіювати посилання", linkCopied: "Посилання скопійовано", reply: "Відповісти", upvote: "Підтримати", downvote: "Не підтримати", loadingPreview: "Перегляд завантажується…", textPreviewFailed: "Не вдалося завантажити текст", loadMoreReplies: "Завантажити більше відповідей", searchPlaceholder: "Пошук у коментарях та авторах…", searchQuery: "Пошуковий запит", search: "Знайти", filters: "Фільтри", author: "Автор", nameOrEmail: "Ім’я або email", fromDate: "Дата від", toDate: "Дата до", sortBy: "Сортувати за", relevance: "Релевантністю", direction: "Напрямок", applyFilters: "Застосувати", reset: "Скинути", searching: "Пошук…", resultsLoaded: "Завантажено: {count}", moreAvailable: "є ще", source: "джерело", searchCriteriaError: "Введіть щонайменше два символи або оберіть фільтр.", searchUnavailable: "Пошук тимчасово недоступний.", noQueryMatches: "Нічого не знайдено за запитом «{query}».", noFilterMatches: "За обраними фільтрами нічого не знайдено.", loadMoreResults: "Завантажити ще",
};

const russian: Messages = {
  tagline: "Содержательные разговоры с понятными связями.", joinDiscussion: "Присоединиться к обсуждению", joinHint: "Поделитесь мыслью или задайте вопрос", comments: "Комментарии", live: "Онлайн", connecting: "Подключение", closed: "Офлайн", sortField: "Поле сортировки", sortDirection: "Направление сортировки", date: "Дата", name: "Имя", email: "Email", descending: "Сначала новые", ascending: "Сначала старые", newComments: "Новых комментариев: {count}", loading: "Загрузка…", emptyThread: "Комментариев пока нет. Начните обсуждение.", loadMoreComments: "Загрузить ещё 25 комментариев", theme: "Тема", auto: "Авто", light: "Светлая", dark: "Тёмная", language: "Язык", signIn: "Войти", register: "Регистрация", signOut: "Выйти", changeAvatar: "Изменить аватар", welcomeBack: "С возвращением", createAccount: "Создать аккаунт", usernameOrEmail: "Имя или email", username: "Имя пользователя", password: "Пароль", pleaseWait: "Подождите…", close: "Закрыть", addComment: "Добавить комментарий", replyTo: "Ответ для {name}", cancel: "Отменить", postingAs: "Вы пишете как", homepage: "Сайт", comment: "Комментарий", write: "Написать", preview: "Просмотр", formatting: "Форматирование", bold: "Жирный", italic: "Курсив", code: "Код", link: "Ссылка", linkUrl: "Адрес ссылки", commentPlaceholder: "Напишите содержательный ответ…", characters: "Символов: {count}", previewFailed: "Не удалось создать просмотр — проверьте закрытие тегов.", attachment: "Вложение", attachmentHint: "JPG, PNG, GIF или TXT", chooseFile: "Выбрать файл", removeAttachment: "Удалить вложение", uploadFailed: "Не удалось загрузить вложение.", captcha: "CAPTCHA", captchaAlt: "Изображение CAPTCHA", captchaLoading: "CAPTCHA загружается…", captchaUnavailable: "CAPTCHA недоступна", newImage: "Новое изображение", sendComment: "Отправить комментарий", sending: "Отправка…", copyLink: "Копировать ссылку", linkCopied: "Ссылка скопирована", reply: "Ответить", upvote: "Поддержать", downvote: "Не поддержать", loadingPreview: "Просмотр загружается…", textPreviewFailed: "Не удалось загрузить текст", loadMoreReplies: "Загрузить больше ответов", searchPlaceholder: "Поиск по комментариям и авторам…", searchQuery: "Поисковый запрос", search: "Найти", filters: "Фильтры", author: "Автор", nameOrEmail: "Имя или email", fromDate: "Дата от", toDate: "Дата до", sortBy: "Сортировать по", relevance: "Релевантности", direction: "Направление", applyFilters: "Применить", reset: "Сбросить", searching: "Поиск…", resultsLoaded: "Загружено: {count}", moreAvailable: "есть ещё", source: "источник", searchCriteriaError: "Введите минимум два символа или выберите фильтр.", searchUnavailable: "Поиск временно недоступен.", noQueryMatches: "По запросу «{query}» ничего не найдено.", noFilterMatches: "По выбранным фильтрам ничего не найдено.", loadMoreResults: "Загрузить ещё",
};

const messages: Record<Locale, Messages> = { en: english, uk: ukrainian, ru: russian };
const localeTags: Record<Locale, string> = { en: "en-US", uk: "uk-UA", ru: "ru-RU" };
const activeLocale = ref<Locale>(Locale.English);

function isLocale(value: string | null): value is Locale {
  return value === Locale.English || value === Locale.Ukrainian || value === Locale.Russian;
}

export function initializeI18n(): void {
  const saved = localStorage.getItem(STORAGE_KEY);
  const browser = navigator.language.slice(0, 2);
  activeLocale.value = isLocale(saved) ? saved : isLocale(browser) ? browser : Locale.English;
  document.documentElement.lang = activeLocale.value;
}

export function setLocale(value: Locale): void {
  activeLocale.value = value;
  localStorage.setItem(STORAGE_KEY, value);
  document.documentElement.lang = value;
}

export function translate(key: MessageKey, params: Record<string, string | number> = {}): string {
  return messages[activeLocale.value][key].replace(/\{(\w+)\}/g, (match, name: string) =>
    params[name] === undefined ? match : String(params[name]),
  );
}

export function formatDate(value: string, dateOnly = false): string {
  return new Intl.DateTimeFormat(localeTags[activeLocale.value], dateOnly
    ? { dateStyle: "medium" }
    : { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function useI18n() {
  return {
    locale: readonly(activeLocale),
    localeTag: computed(() => localeTags[activeLocale.value]),
    setLocale,
    t: translate,
    formatDate,
  };
}
