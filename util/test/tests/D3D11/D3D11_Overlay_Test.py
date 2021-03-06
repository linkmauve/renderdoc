import rdtest
import renderdoc as rd


class D3D11_Overlay_Test(rdtest.TestCase):
    demos_test_name = 'D3D11_Overlay_Test'

    def check_clearbeforedraw_depth(self, out, depthId):
        # Test ClearBeforeDraw with a depth target
        tex = rd.TextureDisplay()
        tex.overlay = rd.DebugOverlay.ClearBeforeDraw
        tex.resourceId = depthId

        out.SetTextureDisplay(tex)
        out.GetDebugOverlayTexID() # Called to refresh the overlay
        
        overlay = rd.DebugOverlay.ClearBeforeDraw
        test_name = str(overlay) + '.Depth'

        overlay_path = rdtest.get_tmp_path(test_name + '.png')
        ref_path = self.get_ref_path(test_name + '.png')

        save_data = rd.TextureSave()
        save_data.resourceId = depthId
        save_data.destType = rd.FileType.PNG
        save_data.channelExtract = 0

        tolerance = 2

        self.controller.SaveTexture(save_data, overlay_path)

        if not rdtest.png_compare(overlay_path, ref_path, tolerance):
            raise rdtest.TestFailureException("Reference and output image differ for overlay {}".format(test_name), overlay_path, ref_path)

        rdtest.log.success("Reference and output image are identical for {}".format(test_name))

    def check_capture(self):
        out: rd.ReplayOutput = self.controller.CreateOutput(rd.CreateHeadlessWindowingData(100, 100), rd.ReplayOutputType.Texture)

        self.check(out is not None)

        test_marker: rd.DrawcallDescription = self.find_draw("Test")

        self.controller.SetFrameEvent(test_marker.next.eventId, True)

        pipe: rd.PipeState = self.controller.GetPipelineState()

        tex = rd.TextureDisplay()
        tex.resourceId = pipe.GetOutputTargets()[0].resourceId

        # Check the actual output is as expected first.

        # Background around the outside
        self.check_pixel_value(tex.resourceId, 0.1, 0.1, [0.2, 0.2, 0.2, 1.0])
        self.check_pixel_value(tex.resourceId, 0.8, 0.1, [0.2, 0.2, 0.2, 1.0])
        self.check_pixel_value(tex.resourceId, 0.5, 0.95, [0.2, 0.2, 0.2, 1.0])

        # Large dark grey triangle
        self.check_pixel_value(tex.resourceId, 0.5, 0.1, [0.1, 0.1, 0.1, 1.0])
        self.check_pixel_value(tex.resourceId, 0.5, 0.9, [0.1, 0.1, 0.1, 1.0])
        self.check_pixel_value(tex.resourceId, 0.2, 0.9, [0.1, 0.1, 0.1, 1.0])
        self.check_pixel_value(tex.resourceId, 0.8, 0.9, [0.1, 0.1, 0.1, 1.0])

        # Red upper half triangle
        self.check_pixel_value(tex.resourceId, 0.3, 0.4, [1.0, 0.0, 0.0, 1.0])
        # Blue lower half triangle
        self.check_pixel_value(tex.resourceId, 0.3, 0.6, [0.0, 0.0, 1.0, 1.0])

        # Floating clipped triangle
        self.check_pixel_value(tex.resourceId, 335, 140, [0.0, 0.0, 0.0, 1.0])
        self.check_pixel_value(tex.resourceId, 340, 140, [0.2, 0.2, 0.2, 1.0])

        # Triangle size triangles
        self.check_pixel_value(tex.resourceId, 200, 51, [1.0, 0.5, 1.0, 1.0])
        self.check_pixel_value(tex.resourceId, 200, 65, [1.0, 1.0, 0.0, 1.0])
        self.check_pixel_value(tex.resourceId, 200, 79, [0.0, 1.0, 1.0, 1.0])
        self.check_pixel_value(tex.resourceId, 200, 93, [0.0, 1.0, 0.0, 1.0])

        for overlay in rd.DebugOverlay:
            if overlay == rd.DebugOverlay.NoOverlay:
                continue

            # These overlays are just displaymodes really, not actually separate overlays
            if overlay == rd.DebugOverlay.NaN or overlay == rd.DebugOverlay.Clipping:
                continue

            # Unfortunately line-fill rendering seems to vary too much by IHV, so gives inconsistent results
            if overlay == rd.DebugOverlay.Wireframe:
                continue

            tex.overlay = overlay
            out.SetTextureDisplay(tex)

            overlay_path = rdtest.get_tmp_path(str(overlay) + '.png')
            ref_path = self.get_ref_path(str(overlay) + '.png')

            save_data = rd.TextureSave()
            save_data.resourceId = out.GetDebugOverlayTexID()
            save_data.destType = rd.FileType.PNG

            save_data.comp.blackPoint = 0.0
            save_data.comp.whitePoint = 1.0

            tolerance = 2

            # These overlays return grayscale above 1, so rescale to an expected range.
            if (overlay == rd.DebugOverlay.QuadOverdrawDraw or overlay == rd.DebugOverlay.QuadOverdrawPass or
                    overlay == rd.DebugOverlay.TriangleSizeDraw or overlay == rd.DebugOverlay.TriangleSizePass):
                save_data.comp.whitePoint = 10.0

            # These overlays modify the underlying texture, so we need to save it out instead of the overlay
            if overlay == rd.DebugOverlay.ClearBeforeDraw or overlay == rd.DebugOverlay.ClearBeforePass:
                save_data.resourceId = tex.resourceId

            self.controller.SaveTexture(save_data, overlay_path)

            if not rdtest.png_compare(overlay_path, ref_path, tolerance):
                raise rdtest.TestFailureException("Reference and output image differ for overlay {}".format(str(overlay)), overlay_path, ref_path)

            rdtest.log.success("Reference and output image are identical for {}".format(str(overlay)))

        save_data = rd.TextureSave()
        save_data.resourceId = pipe.GetDepthTarget().resourceId
        save_data.destType = rd.FileType.PNG
        save_data.channelExtract = 0

        tmp_path = rdtest.get_tmp_path('depth.png')
        ref_path = self.get_ref_path('depth.png')

        self.controller.SaveTexture(save_data, tmp_path)

        if not rdtest.png_compare(tmp_path, ref_path):
            raise rdtest.TestFailureException("Reference and output image differ for depth {}", tmp_path, ref_path)

        rdtest.log.success("Reference and output image are identical for depth")

        save_data.channelExtract = 1

        tmp_path = rdtest.get_tmp_path('stencil.png')
        ref_path = self.get_ref_path('stencil.png')

        self.controller.SaveTexture(save_data, tmp_path)

        if not rdtest.png_compare(tmp_path, ref_path):
            raise rdtest.TestFailureException("Reference and output image differ for stencil {}", tmp_path, ref_path)

        rdtest.log.success("Reference and output image are identical for stencil")

        self.check_clearbeforedraw_depth(out, pipe.GetDepthTarget().resourceId)

        out.Shutdown()
