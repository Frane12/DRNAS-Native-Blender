  private final class DrnasPointer extends View {
    final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    final android.graphics.Path arrow = new android.graphics.Path();
    final android.graphics.Shader fill = new android.graphics.LinearGradient(4, 4, 19, 28,
        Color.rgb(251, 254, 255), Color.rgb(191, 228, 240), android.graphics.Shader.TileMode.CLAMP);
    DrnasPointer() {
      super(BlenderActivity.this);
      paint.setStrokeJoin(android.graphics.Paint.Join.ROUND);
      paint.setStrokeCap(android.graphics.Paint.Cap.ROUND);
      arrow.moveTo(4, 4.8f);
      arrow.quadTo(4, 3.6f, 5, 4.3f);
      arrow.lineTo(22.2f, 15.1f);
      arrow.quadTo(23.5f, 16, 21.8f, 16.1f);
      arrow.lineTo(14.2f, 16.3f);
      arrow.lineTo(18.6f, 25.7f);
      arrow.quadTo(19, 26.5f, 18.2f, 26.9f);
      arrow.lineTo(15.8f, 28);
      arrow.quadTo(15, 28.4f, 14.6f, 27.5f);
      arrow.lineTo(10.1f, 18.2f);
      arrow.lineTo(5.2f, 23.6f);
      arrow.quadTo(4, 24.9f, 4, 23.2f);
      arrow.close();
    }
    @Override protected void onDraw(android.graphics.Canvas canvas) {
      super.onDraw(canvas);
      float scale = getResources().getDisplayMetrics().density * drnasCursorPercent / 100f;
      canvas.save(); canvas.scale(scale, scale);
      paint.setShader(null); paint.setStyle(android.graphics.Paint.Style.FILL);
      if (drnasPointerEffect && (drnasHeldMouseButtons != 0
          || android.os.SystemClock.uptimeMillis() < drnasClickEffectUntil)) {
        paint.setColor(Color.argb(75, 91, 218, 235));
        canvas.drawCircle(12, 12, 11, paint);
      }
      canvas.save(); canvas.translate(0.5f, 1.1f);
      paint.setColor(Color.argb(105, 3, 12, 23)); canvas.drawPath(arrow, paint); canvas.restore();
      paint.setShader(fill); canvas.drawPath(arrow, paint); paint.setShader(null);
      paint.setStyle(android.graphics.Paint.Style.STROKE); paint.setStrokeWidth(1.15f);
      paint.setColor(Color.rgb(16, 37, 51)); canvas.drawPath(arrow, paint);
      paint.setStyle(android.graphics.Paint.Style.FILL);
      canvas.restore();
    }
  }
