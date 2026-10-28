{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "tempinfocli";
  version = "0.3.0";
  format = "pyproject";

  src = pkgs.lib.cleanSource ./.;

  nativeBuildInputs = with pkgs.python3Packages; [
    setuptools
  ];

  nativeCheckInputs = with pkgs.python3Packages; [
    pytestCheckHook
  ];

  pythonImportsCheck = [ "tempinfocli" ];

  propagatedBuildInputs = with pkgs.python3Packages; [
    rich
    psutil
  ];

  makeWrapperArgs = pkgs.lib.optionals pkgs.stdenv.isLinux [
    "--prefix" "PATH" ":" (pkgs.lib.makeBinPath [ pkgs.pciutils ])
  ];

  postInstall = ''
    install -Dm644 packaging/linux/tempinfo.desktop $out/share/applications/tempinfo.desktop
    install -Dm644 assets/tempinfo.svg $out/share/icons/hicolor/scalable/apps/tempinfo.svg
    for size in 16 32 48 64 128 256; do
      install -Dm644 assets/tempinfo-$size.png $out/share/icons/hicolor/''${size}x''${size}/apps/tempinfo.png
    done
  '';

  meta = with pkgs.lib; {
    description = "A live terminal temperature dashboard";
    license = licenses.mit;
    mainProgram = "tempinfo";
  };
}
