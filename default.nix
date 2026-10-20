{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "tempinfocli";
  version = "0.1.0";
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

  meta = with pkgs.lib; {
    description = "A live terminal temperature dashboard";
    license = licenses.mit;
    mainProgram = "tempinfocli";
  };
}
