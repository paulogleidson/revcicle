import Button from './Button'

export default function ConfirmModal({
  aberto,
  titulo,
  mensagem,
  textoConfirmar = 'Confirmar',
  textoCancelar = 'Cancelar',
  confirmando = false,
  destrutivo = false,
  onConfirmar,
  onCancelar,
}) {
  if (!aberto) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-titulo"
    >
      {/* Overlay: clicar fora cancela (quando não está processando) */}
      <button
        type="button"
        aria-label="Fechar"
        onClick={confirmando ? undefined : onCancelar}
        className="absolute inset-0 bg-black/60"
      />

      <div className="relative bg-app-surface border border-app-line rounded-xl shadow-2xl max-w-sm w-full p-5 space-y-4">
        <h2
          id="confirm-modal-titulo"
          className="text-lg font-semibold text-app-fg"
        >
          {titulo}
        </h2>
        {mensagem && <p className="text-sm text-app-muted">{mensagem}</p>}
        <div className="flex gap-2 justify-end">
          <Button
            variante="secundario"
            onClick={onCancelar}
            disabled={confirmando}
          >
            {textoCancelar}
          </Button>
          <Button
            variante={destrutivo ? 'perigo' : 'primario'}
            onClick={onConfirmar}
            disabled={confirmando}
          >
            {confirmando ? '…' : textoConfirmar}
          </Button>
        </div>
      </div>
    </div>
  )
}
