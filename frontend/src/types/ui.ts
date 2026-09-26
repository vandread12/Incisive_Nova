/**
 * TypeScript interfaces for UI components (SPEC-08).
 * 
 * These types are specific to the Next.js frontend dashboard
 * and UI components using shadcn/ui and TanStack Query.
 */

import type {
  OrdenB2BUI,
  OrderStatus,
  OrderLifecycleStep,
  OrderLifecycleStepInfo,
} from './settlement';
import { EXAMPLE_ORDEN_B2B_UI } from './settlement';
import type { AuthState, StellarWalletInfo } from './auth';

// Dashboard layout types
export interface DashboardLayoutProps {
  /** Información de sesión del usuario */
  session: AuthState;
  /** Elementos hijos */
  children: React.ReactNode;
  /** Título de la página */
  pageTitle?: string;
  /** Indica si está cargando */
  isLoading?: boolean;
}

export interface SidebarItem {
  /** ID único del item */
  id: string;
  /** Etiqueta del item */
  label: string;
  /** Icono del item */
  icon?: React.ReactNode;
  /** Ruta del item */
  href: string;
  /** Indica si está activo */
  active?: boolean;
  /** Subitems */
  subItems?: SidebarItem[];
  /** Permisos requeridos */
  requiredPermissions?: string[];
}

export interface DashboardHeaderProps {
  /** Información de sesión del usuario */
  session: AuthState;
  /** Información de la wallet conectada */
  wallet?: StellarWalletInfo;
  /** Título de la página */
  pageTitle?: string;
  /** Acciones del header */
  actions?: React.ReactNode;
  /** Indica si está cargando */
  isLoading?: boolean;
}

// Data table types (TanStack Table + shadcn/ui)
export interface ColumnDefinition<T> {
  /** ID de la columna */
  id: string;
  /** Encabezado de la columna */
  header: string | ((props: any) => React.ReactNode);
  /** Celda de la columna */
  cell: (props: { row: { original: T } }) => React.ReactNode;
  /** Indica si la columna es ordenable */
  sortable?: boolean;
  /** Indica si la columna es filtrable */
  filterable?: boolean;
  /** Ancho de la columna */
  width?: number | string;
  /** Indica si la columna está oculta */
  hidden?: boolean;
  /** Metadatos de la columna */
  meta?: Record<string, any>;
}

export interface OrdersDataTableProps {
  /** Datos de las órdenes */
  data: OrdenB2BUI[];
  /** Estado de carga */
  isLoading?: boolean;
  /** Error de carga */
  error?: string;
  /** Función para recargar datos */
  onRefresh?: () => void;
  /** Configuración de columnas */
  columns?: ColumnDefinition<OrdenB2BUI>[];
  /** Configuración de paginación */
  pagination?: {
    /** Página actual */
    page: number;
    /** Tamaño de página */
    pageSize: number;
    /** Total de elementos */
    total: number;
    /** Función para cambiar de página */
    onPageChange: (page: number) => void;
    /** Función para cambiar el tamaño de página */
    onPageSizeChange: (pageSize: number) => void;
  };
  /** Configuración de filtros */
  filters?: {
    /** Filtros aplicados */
    applied: Record<string, any>;
    /** Función para aplicar filtros */
    onFilterChange: (filters: Record<string, any>) => void;
    /** Opciones de filtro disponibles */
    options: Record<string, { label: string; value: any }[]>;
  };
}

// Order lifecycle stepper types
// El tipo canónico OrderLifecycleStep y la interfaz base OrderLifecycleStepInfo
// viven en './settlement'. Aquí se extienden con campos específicos de UI.
export interface OrderLifecycleStepUIInfo extends OrderLifecycleStepInfo {
  /** Icono del paso */
  icon?: React.ReactNode;
  /** Etiqueta del paso */
  label: string;
  /** Descripción del paso */
  description?: string;
}

export interface OrderLifecycleStepperProps {
  /** Pasos del ciclo de vida (enriquecidos para UI) */
  steps: OrderLifecycleStepUIInfo[];
  /** Paso actual */
  currentStep: OrderLifecycleStep;
  /** Estado general */
  overallStatus: OrderStatus;
  /** Indica si está cargando */
  isLoading?: boolean;
  /** Función para expandir/contraer */
  onToggleExpand?: (expanded: boolean) => void;
  /** Indica si está expandido */
  expanded?: boolean;
}

// Notification system types
export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  /** ID único de la notificación */
  id: string;
  /** Tipo de notificación */
  type: NotificationType;
  /** Título de la notificación */
  title: string;
  /** Mensaje de la notificación */
  message: string;
  /** Tiempo de vida en segundos */
  duration?: number;
  /** Indica si se puede descartar */
  dismissible?: boolean;
  /** Acción opcional */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Timestamp de creación */
  createdAt: string;
  /** Indica si fue leída */
  read: boolean;
}

export interface NotificationCenterProps {
  /** Notificaciones */
  notifications: Notification[];
  /** Función para marcar como leída */
  onMarkAsRead: (id: string) => void;
  /** Función para descartar */
  onDismiss: (id: string) => void;
  /** Función para marcar todas como leídas */
  onMarkAllAsRead: () => void;
  /** Función para limpiar todas */
  onClearAll: () => void;
  /** Indica si está abierto */
  open?: boolean;
  /** Función para cambiar estado */
  onOpenChange?: (open: boolean) => void;
}

// Real-time updates types
export interface RealTimeUpdate<T = any> {
  /** Tipo de actualización */
  type: 'create' | 'update' | 'delete' | 'status_change';
  /** ID del elemento */
  id: string;
  /** Datos actualizados */
  data: T;
  /** Timestamp de la actualización */
  timestamp: string;
  /** Fuente de la actualización */
  source: string;
}

export interface UseRealTimeUpdatesOptions<T> {
  /** URL del WebSocket */
  websocketUrl: string;
  /** Canales a suscribir */
  channels: string[];
  /** Función para manejar actualizaciones */
  onUpdate: (update: RealTimeUpdate<T>) => void;
  /** Función para manejar conexión */
  onConnect?: () => void;
  /** Función para manejar desconexión */
  onDisconnect?: () => void;
  /** Función para manejar errores */
  onError?: (error: any) => void;
  /** Auto-reconectar */
  autoReconnect?: boolean;
  /** Delay de reconexión en ms */
  reconnectDelay?: number;
}

// Theme types
export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeConfig {
  /** Modo del tema */
  mode: ThemeMode;
  /** Colores primarios */
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    border: string;
  };
  /** Tipografía */
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  /** Espaciado */
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  /** Bordes redondeados */
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
}

// Form types
export interface FormField<T = any> {
  /** Nombre del campo */
  name: string;
  /** Etiqueta del campo */
  label: string;
  /** Tipo del campo */
  type: 'text' | 'number' | 'select' | 'checkbox' | 'radio' | 'date' | 'textarea';
  /** Valor por defecto */
  defaultValue?: T;
  /** Indica si es requerido */
  required?: boolean;
  /** Validación personalizada */
  validate?: (value: T) => string | undefined;
  /** Opciones para select/radio */
  options?: Array<{ label: string; value: T }>;
  /** Placeholder */
  placeholder?: string;
  /** Ayuda/descripción */
  helpText?: string;
  /** Indica si está deshabilitado */
  disabled?: boolean;
  /** Indica si está oculto */
  hidden?: boolean;
  /** Metadatos del campo */
  meta?: Record<string, any>;
}

export interface FormSchema<T = any> {
  /** Campos del formulario */
  fields: FormField[];
  /** Valores iniciales */
  initialValues?: Partial<T>;
  /** Función para enviar */
  onSubmit: (values: T) => Promise<void>;
  /** Función para validar */
  validate?: (values: T) => Record<string, string>;
  /** Etiqueta del botón de enviar */
  submitLabel?: string;
  /** Indica si está cargando */
  isLoading?: boolean;
}

// Loading states
export interface LoadingState {
  /** Indica si está cargando */
  isLoading: boolean;
  /** Tipo de carga */
  type?: 'skeleton' | 'spinner' | 'progress';
  /** Mensaje de carga */
  message?: string;
  /** Progreso (0-100) */
  progress?: number;
}

// Error boundary types
export interface ErrorBoundaryProps {
  /** Elementos hijos */
  children: React.ReactNode;
  /** Función para manejar errores */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** Componente de fallback */
  fallback?: React.ReactNode;
}

export interface ErrorBoundaryState {
  /** Indica si hay un error */
  hasError: boolean;
  /** Error capturado */
  error?: Error;
  /** Información del error */
  errorInfo?: React.ErrorInfo;
}

// API client types
export interface ApiClientConfig {
  /** URL base de la API */
  baseUrl: string;
  /** Timeout en ms */
  timeout?: number;
  /** Headers por defecto */
  headers?: Record<string, string>;
  /** Interceptores de request */
  requestInterceptors?: Array<(config: any) => any>;
  /** Interceptores de response */
  responseInterceptors?: Array<(response: any) => any>;
}

export interface ApiResponse<T = any> {
  /** Indica si la petición fue exitosa */
  success: boolean;
  /** Datos de la respuesta */
  data?: T;
  /** Error si la petición falló */
  error?: {
    /** Código de error */
    code: string;
    /** Mensaje de error */
    message: string;
    /** Detalles del error */
    details?: any;
  };
  /** Metadatos de la respuesta */
  metadata?: {
    /** Timestamp de la respuesta */
    timestamp: string;
    /** ID de la solicitud */
    requestId: string;
    /** Tiempo de procesamiento en ms */
    processingTimeMs?: number;
  };
}

// Query hooks types (TanStack Query v5)
export interface UseQueryOptions<T = any> {
  /** Clave de la query */
  queryKey: any[];
  /** Función para obtener datos */
  queryFn: () => Promise<T>;
  /** Opciones de TanStack Query */
  options?: {
    enabled?: boolean;
    retry?: number | boolean;
    retryDelay?: number;
    staleTime?: number;
    cacheTime?: number;
    refetchOnMount?: boolean | 'always';
    refetchOnWindowFocus?: boolean | 'always';
    refetchOnReconnect?: boolean | 'always';
    refetchInterval?: number | false;
    onSuccess?: (data: T) => void;
    onError?: (error: any) => void;
    onSettled?: (data: T | undefined, error: any | null) => void;
  };
}

export interface UseMutationOptions<T = any, V = any> {
  /** Función de mutación */
  mutationFn: (variables: V) => Promise<T>;
  /** Opciones de TanStack Query */
  options?: {
    onSuccess?: (data: T, variables: V) => void;
    onError?: (error: any, variables: V) => void;
    onSettled?: (data: T | undefined, error: any | null, variables: V) => void;
    retry?: number | boolean;
    retryDelay?: number;
  };
}

// Example objects for testing
export const EXAMPLE_NOTIFICATION: Notification = {
  id: 'notification_123',
  type: 'success',
  title: 'Orden liquidada',
  message: 'La orden order_123456 ha sido liquidada exitosamente',
  duration: 5000,
  dismissible: true,
  action: {
    label: 'Ver detalles',
    onClick: () => console.log('Ver detalles')
  },
  createdAt: '2026-09-25T10:00:00Z',
  read: false
};

export const EXAMPLE_REAL_TIME_UPDATE: RealTimeUpdate<OrdenB2BUI> = {
  type: 'status_change',
  id: 'order_123456',
  data: EXAMPLE_ORDEN_B2B_UI,
  timestamp: '2026-09-25T10:05:00Z',
  source: 'settlement_engine'
};

export const EXAMPLE_FORM_FIELD: FormField<string> = {
  name: 'amount',
  label: 'Monto',
  type: 'number',
  required: true,
  placeholder: 'Ingrese el monto',
  helpText: 'Monto mínimo: 10.00 EUR',
  validate: (value) => {
    if (!value) return 'El monto es requerido';
    if (parseFloat(value) < 10) return 'El monto mínimo es 10.00 EUR';
    return undefined;
  }
};